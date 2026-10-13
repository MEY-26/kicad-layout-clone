"""Small synthetic SMD footprint with separate paste apertures."""
import uuid
from kipy.board_types import FootprintInstance, Pad, BoardShape
from kipy.geometry import Vector2, Angle
from kipy.proto.board.board_types_pb2 import BoardLayer as L


def footprint(ref,courtyard):
    fp=FootprintInstance()
    fp.proto.id.value=str(uuid.uuid5(uuid.NAMESPACE_URL,ref))
    fp.reference_field.text.value=ref
    fp.layer=L.BL_F_Cu
    fp.position=Vector2.from_xy_mm(10 if ref=='R1' else 20,10)
    fp.orientation=Angle.from_degrees(0)
    items=[]
    for number,x in [('1',-320000),('2',320000)]:
        pad=Pad()
        pad.proto.id.value=str(uuid.uuid5(uuid.NAMESPACE_URL,ref+number))
        pad.number=number
        pad.proto.type=2
        pad.position=Vector2.from_xy(fp.position.x+x,fp.position.y)
        pad.proto.net.name=ref+'-net-'+number
        pad.proto.pad_stack.layers.extend([L.BL_F_Cu,L.BL_F_Mask])
        pad.proto.pad_stack.copper_layers[0].size.x_nm=300000
        pad.proto.pad_stack.copper_layers[0].size.y_nm=350000
        paste=Pad(pad.proto)
        paste.proto.id.value=str(uuid.uuid5(uuid.NAMESPACE_URL,ref+'-paste-'+number))
        paste.number=''
        paste.proto.net.Clear()
        paste.proto.position.x_nm+=-25000 if number=='1' else 25000
        del paste.proto.pad_stack.layers[:]
        paste.proto.pad_stack.layers.append(L.BL_F_Paste)
        items.extend([paste,pad])
    if courtyard:
        shape=BoardShape()
        shape.proto.id.value=str(uuid.uuid5(uuid.NAMESPACE_URL,ref+'-courtyard'))
        shape.layer=L.BL_F_CrtYd
        shape.proto.shape.segment.start.CopyFrom(Vector2.from_xy_mm(19,9).proto)
        shape.proto.shape.segment.end.CopyFrom(Vector2.from_xy_mm(21,9).proto)
        items.append(shape)
    fp.definition.items=items
    return fp
