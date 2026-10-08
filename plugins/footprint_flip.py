"""KiCad-compatible TOP_BOTTOM reflection of a disposable source template.

Board Y is reflected and footprint orientation negated. The placement helper
then aligns this template to the target, whose position/angle/side stay intact.
"""
from kipy.board_types import FootprintInstance, Pad, BoardShape, BoardText
from kipy.proto.board.board_types_pb2 import BoardLayer, PadStackType
from core import LayoutError


def flip_layer(layer, copper_count):
    name = BoardLayer.Name(layer)
    if name.startswith('BL_In') and name.endswith('_Cu'):
        index = int(name[5:-3])
        if not 1 <= index <= copper_count - 2:
            raise LayoutError('İç bakır katmanı kartın katman yapısıyla uyumsuz.')
        return getattr(BoardLayer, f'BL_In{copper_count - 1 - index}_Cu')
    if name.startswith(('BL_F_', 'BL_B_')):
        opposite = 'BL_B_' if name.startswith('BL_F_') else 'BL_F_'
        return getattr(BoardLayer, opposite + name[5:], layer)
    return layer


def mirror_points(message, center_y):
    if message.DESCRIPTOR.full_name == 'kiapi.common.types.Vector2':
        message.y_nm = 2 * center_y - message.y_nm
        return
    for field, value in message.ListFields():
        if field.message_type and field.name != 'attributes':
            if field.label == field.LABEL_REPEATED:
                for child in value:
                    mirror_points(child, center_y)
            else:
                mirror_points(value, center_y)


def swap_messages(message, first, second):
    a, b = getattr(message, first), getattr(message, second)
    saved = type(a)(); saved.CopyFrom(a)
    present_a, present_b = message.HasField(first), message.HasField(second)
    a.CopyFrom(b); b.CopyFrom(saved)
    if not present_b: message.ClearField(first)
    if not present_a: message.ClearField(second)


def mirror_text(board_text, center_y, copper_count):
    board_text.text.position.y_nm = 2 * center_y - board_text.text.position.y_nm
    angle = board_text.text.attributes.angle
    angle.value_degrees = (180 - angle.value_degrees + 180) % 360 - 180
    opposite = flip_layer(board_text.layer, copper_count)
    if opposite != board_text.layer:
        board_text.text.attributes.mirrored = not board_text.text.attributes.mirrored
    board_text.layer = opposite


def mirror_pad(pad, center_y, copper_count):
    pad.proto.position.y_nm = 2 * center_y - pad.proto.position.y_nm
    stack = pad.proto.pad_stack
    stack.angle.value_degrees = (-stack.angle.value_degrees + 180) % 360 - 180
    for layer in stack.copper_layers:
        layer.offset.y_nm = -layer.offset.y_nm
        if layer.HasField('trapezoid_delta'):
            layer.trapezoid_delta.y_nm = -layer.trapezoid_delta.y_nm
        if layer.HasField('chamfered_corners'):
            corners = layer.chamfered_corners
            corners.top_left, corners.bottom_left = corners.bottom_left, corners.top_left
            corners.top_right, corners.bottom_right = corners.bottom_right, corners.top_right
        for primitive in layer.custom_shapes:
            mirror_points(primitive.shape, 0)
            primitive.layer = flip_layer(primitive.layer, copper_count)
        if stack.type == PadStackType.PST_CUSTOM:
            layer.layer = flip_layer(layer.layer, copper_count)
        elif stack.type == PadStackType.PST_FRONT_INNER_BACK and layer.layer in (BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu):
            layer.layer = flip_layer(layer.layer, copper_count)
    records = sorted(stack.copper_layers, key=lambda layer: layer.layer)
    del stack.copper_layers[:]; stack.copper_layers.extend(records)
    layers = [flip_layer(layer, copper_count) for layer in stack.layers]
    del stack.layers[:]; stack.layers.extend(layers)
    for name in ('drill', 'secondary_drill', 'tertiary_drill'):
        if stack.HasField(name):
            drill = getattr(stack, name)
            drill.start_layer = flip_layer(drill.start_layer, copper_count)
            drill.end_layer = flip_layer(drill.end_layer, copper_count)
    swap_messages(stack, 'front_outer_layers', 'back_outer_layers')
    swap_messages(stack, 'front_post_machining', 'back_post_machining')


def flipped_template(source, copper_count):
    template = FootprintInstance(source.proto)
    center_y = template.position.y
    # Custom fields, models and zones stay on the target, so exclude unused
    # source children rather than partially transforming them.
    template.definition.items = [item for item in template.definition.items
        if isinstance(item, (Pad, BoardShape, BoardText))]
    for pad in template.definition.pads:
        mirror_pad(pad, center_y, copper_count)
    for item in template.definition.items:
        if isinstance(item, BoardShape):
            mirror_points(item.proto.shape, center_y)
            item.layer = flip_layer(item.layer, copper_count)
        elif isinstance(item, BoardText):
            mirror_text(item.proto, center_y, copper_count)
    for name in ('reference_field', 'value_field', 'datasheet_field', 'description_field'):
        mirror_text(getattr(template, name).proto.text, center_y, copper_count)
    template.proto.orientation.value_degrees = (-template.orientation.degrees + 180) % 360 - 180
    template.layer = flip_layer(template.layer, copper_count)
    return template
