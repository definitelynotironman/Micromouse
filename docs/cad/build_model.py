"""
Micromouse CAD model, built from photos of my mouse. Run: python build_model.py
Axes: X forward, Y left, Z up. Units: mm. Wheel axle at x = 0.
Known numbers from the code: wheel radius 32.5 mm, wheel centres 52.5 mm from the middle.
"""
import math
import cadquery as cq

C = {
    "pcb": cq.Color(0.12, 0.60, 0.31),
    "pcb_dark": cq.Color(0.09, 0.47, 0.25),
    "yellow": cq.Color(0.98, 0.84, 0.05),
    "black": cq.Color(0.09, 0.09, 0.10),
    "tyre": cq.Color(0.07, 0.07, 0.07),
    "rim": cq.Color(0.93, 0.93, 0.91),
    "metal": cq.Color(0.75, 0.76, 0.78),
    "gold": cq.Color(0.83, 0.68, 0.30),
    "white": cq.Color(0.96, 0.96, 0.95),
    "orange": cq.Color(0.95, 0.68, 0.18),
    "chip": cq.Color(0.13, 0.13, 0.14),
}

WHEEL_R = 32.5
AXLE_Z = WHEEL_R
WHEEL_Y = 52.5
WHEEL_W = 26.0
PCB_Z = 16.0
PCB_T = 1.6
TOP = PCB_Z + PCB_T


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl_x(r, x0, x1, y, z):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def cyl_y(r, y0, y1, x, z):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def cyl_z(r, z0, z1, x, y):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


# ---------------------------------------------------------------- wheel
def tyre():
    """Tyre along the Z axis, centred on the origin."""
    t = (cq.Workplane("XY").circle(WHEEL_R).circle(25.0).extrude(WHEEL_W)
         .translate((0, 0, -WHEEL_W / 2)))
    t = t.faces(">Z or <Z").edges().fillet(2.0)
    # tread: two staggered rows of blocks, and a centre groove
    n = 30
    cuts = None
    for row, zc in ((0, -6.0), (1, 6.0)):
        for i in range(n):
            a = 360.0 / n * (i + 0.5 * row)
            g = (cq.Workplane("XY").box(2.6, 4.0, 8.0)
                 .translate((WHEEL_R, 0, zc)).rotate((0, 0, 0), (0, 0, 1), a))
            cuts = g if cuts is None else cuts.union(g)
    groove = (cq.Workplane("XY").circle(WHEEL_R + 1).circle(WHEEL_R - 1.0)
              .extrude(1.6).translate((0, 0, -0.8)))
    return t.cut(cuts).cut(groove)


def rim():
    r = (cq.Workplane("XY").circle(25.0).circle(21.5).extrude(22).translate((0, 0, -11)))
    face = cq.Workplane("XY").circle(25.0).extrude(2.6).translate((0, 0, 8.4))
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        face = face.cut(cyl_z(4.0, 0, 20, 14.5 * math.cos(a), 14.5 * math.sin(a)))
    hub = cq.Workplane("XY").circle(7.5).circle(2.4).extrude(10).translate((0, 0, 2))
    ring = cq.Workplane("XY").circle(11).circle(7.5).extrude(1.2).translate((0, 0, 11))
    return r.union(face).union(hub).union(ring)


def place_wheel(shape, side):
    # local +Z becomes outward (+Y for the left wheel, -Y for the right)
    s = shape.rotate((0, 0, 0), (1, 0, 0), -90 if side > 0 else 90)
    return s.translate((0, side * WHEEL_Y, AXLE_Z))


# ---------------------------------------------------------------- motors
GB_X0, GB_X1 = -26.0, 11.0          # gearbox, output shaft at x = 0
CAN_X0 = -52.0                      # back of the motor can
M_IN, M_OUT = 20.7, 39.5            # inner and outer face of the motor (|y|)


def motor(side):
    y0, y1 = sorted((side * M_IN, side * M_OUT))
    gb = box(GB_X0, GB_X1, y0, y1, AXLE_Z - 11.25, AXLE_Z + 11.25).edges("|Y").fillet(2.5)
    can = cyl_x(11.0, CAN_X0, GB_X0, (y0 + y1) / 2, AXLE_Z).intersect(
        box(CAN_X0 - 1, GB_X0 + 1, y0, y1, 0, 60))
    shaft = cyl_y(2.7, min(side * M_OUT, side * (WHEEL_Y - 8)), max(side * M_OUT, side * (WHEEL_Y - 8)), 0, AXLE_Z)
    return gb.union(can).union(shaft)


def encoder(side):
    yc = side * (M_IN + M_OUT) / 2
    board = box(CAN_X0 - 2.2, CAN_X0 - 1.0, yc - 10, yc + 10, AXLE_Z - 11, AXLE_Z + 11)
    cap = cyl_x(7.5, CAN_X0 - 8.5, CAN_X0 - 2.2, yc, AXLE_Z)
    cap = cap.faces("<X").edges().fillet(1.2).cut(cyl_x(1.4, CAN_X0 - 9, CAN_X0 - 7, yc, AXLE_Z))
    return board, cap


# ---------------------------------------------------------------- PCBs
SENSE_Z = 19.6                      # the sensor board sits a little above the main board
SENSE_TOP = SENSE_Z + PCB_T


def ring_pads(points, z, r_out=0.95):
    s = None
    for x, y in points:
        p = cyl_z(r_out, z, z + 0.12, x, y)
        s = p if s is None else s.union(p)
    return s


def main_pcb():
    s = (cq.Workplane("XY").center(-35, 0).circle(40).extrude(PCB_T)
         .union(cq.Workplane("XY").center(-2.5, 0).rect(65, 74).extrude(PCB_T)))
    for x, y in ((-62, 18), (-62, -18), (-35, 32), (-35, -32)):
        s = s.cut(cyl_z(1.6, -1, 3, x, y))
    return s.translate((0, 0, PCB_Z))


def aux_header_pads():
    # the 2 x 8 "FRONT AUX HEADER" holes in front of the STM32 board
    pts = [(x, -8.9 + i * 2.54) for x in (12.0, 14.54) for i in range(8)]
    return ring_pads(pts, TOP)


def sensor_pcb():
    body = cq.Workplane("XY").polyline([(33, -48.5), (60, -48.5), (72, -36.5), (72, 36.5),
                                        (60, 48.5), (33, 48.5)]).close().extrude(PCB_T)
    tab = cq.Workplane("XY").center(30.5, 0).rect(9, 46).extrude(PCB_T)
    s = body.union(tab)
    for x, y in ((40, 30), (40, -30), (64, 18), (64, -18), (37, 0)):
        s = s.cut(cyl_z(1.5, -1, 3, x, y))
    return s.translate((0, 0, SENSE_Z))


def sensor_header():
    # 2 x 16 pin header joining the sensor board to the main board
    spacer = box(26.8, 32.0, -20.6, 20.6, SENSE_TOP, SENSE_TOP + 2.5)
    pins = None
    for x in (28.13, 30.67):
        for i in range(16):
            y = -19.05 + i * 2.54
            p = box(x - 0.32, x + 0.32, y - 0.32, y + 0.32, SENSE_TOP + 2.5, SENSE_TOP + 6.0)
            pins = p if pins is None else pins.union(p)
    return spacer, pins


def sensor_pads():
    pts = []
    for side in (1, -1):                       # J7 and J8, 6 holes on a 45 degree line
        for i in range(6):
            pts.append((50 + i * 1.8, side * (17 + i * 1.8)))
    for x, y in ((44, 10), (44, -10), (46.5, 10), (46.5, -10), (52, 6), (52, -6)):
        pts.append((x, y))
    for side in (1, -1):                       # 4 holes near the side sensors
        for i in range(4):
            pts.append((38 + i * 2.54, side * 38))
    return ring_pads(pts, SENSE_TOP)


def tof_board_front():
    b = box(69.0, 70.2, -8, 8, SENSE_TOP + 1, SENSE_TOP + 13)
    chip = box(70.2, 71.4, -2.5, 2.5, SENSE_TOP + 6, SENSE_TOP + 9)
    hdr = box(64.5, 69.0, -7.6, 7.6, SENSE_TOP, SENSE_TOP + 3.2)
    return b, chip, hdr


def tof_board_side(side):
    y0 = side * 43.0
    b = box(44, 60, min(y0, y0 + side * 1.2), max(y0, y0 + side * 1.2), SENSE_TOP + 1, SENSE_TOP + 13)
    yc = y0 + side * 1.2
    chip = box(49.5, 54.5, min(yc, yc + side * 1.2), max(yc, yc + side * 1.2), SENSE_TOP + 6, SENSE_TOP + 9)
    hdr = box(44.4, 59.6, min(y0, y0 - side * 3.5), max(y0, y0 - side * 3.5), SENSE_TOP, SENSE_TOP + 3.2)
    return b, chip, hdr


def socket_4pin():
    return box(55, 57.6, -5.1, 5.1, SENSE_TOP, SENSE_TOP + 8.5)


PROC_Z = 38.0
PROC_TOP = PROC_Z + PCB_T


def processor():
    board = box(-46, 4, -20, 20, PROC_Z, PROC_TOP)
    # the STM32L476 sits turned 45 degrees on this board
    qfp = (box(-7, 7, -7, 7, PROC_TOP + 0.3, PROC_TOP + 1.7)
           .rotate((0, 0, 0), (0, 0, 1), 45).translate((-19, 0, 0)))
    legs = (box(-8, 8, -8, 8, PROC_TOP, PROC_TOP + 0.35)
            .rotate((0, 0, 0), (0, 0, 1), 45).translate((-19, 0, 0)))
    usb = box(-47, -40, -4, 4, PROC_TOP, PROC_TOP + 3.0)
    stack = box(-44, 2, 16.5, 19.4, TOP, PROC_Z).union(box(-44, 2, -19.4, -16.5, TOP, PROC_Z))
    sock = box(-45.5, -25, 11.2, 13.8, PROC_TOP, PROC_TOP + 8.5)
    parts = None
    for (x, y, w, h) in ((-37, -9, 3, 2), (-35, -13, 2, 1.2), (-31, -12, 3, 2), (-4, 9, 2, 1.2), (-4, 4, 2, 1.2),
                         (-4, -1, 2, 1.2), (-6, -9, 3, 3), (-30, 8, 4, 2.4), (-9, 12, 1.6, 1), (-26, -9, 1.6, 1)):
        p = box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, PROC_TOP, PROC_TOP + 0.9)
        parts = p if parts is None else parts.union(p)
    btn_base, btn_cap = None, None
    for (x, y) in ((-1, 11), (-1, -11), (-36, 10)):
        b = box(x - 2.4, x + 2.4, y - 2.4, y + 2.4, PROC_TOP, PROC_TOP + 1.5)
        c = cyl_z(1.3, PROC_TOP + 1.5, PROC_TOP + 2.3, x, y)
        btn_base = b if btn_base is None else btn_base.union(b)
        btn_cap = c if btn_cap is None else btn_cap.union(c)
    pts = [(-44.5 + i * 2.54, y) for i in range(19) for y in (18.4, 15.86, -15.86, -18.4)]
    pads = ring_pads(pts, PROC_TOP, 0.85)
    return board, qfp, legs, usb, stack, sock, parts, btn_base, btn_cap, pads


def battery():
    return box(-38, 0, -13, 13, TOP + 0.5, TOP + 9).edges("|Z").fillet(2)


# ---------------------------------------------------------------- yellow 3D printed parts
GB_TOP = AXLE_Z + 11.25
BT = 3.2                            # bracket thickness


def bracket(side):
    s = 1 if side > 0 else -1

    def by(a, b):
        return min(s * a, s * b), max(s * a, s * b)

    z0, z1 = GB_TOP, GB_TOP + BT
    # a frame over the motor: two long rails, a rear bar and a front bar, with a window between
    parts = [
        box(-50, 16, *by(32.5, 39.3), z0, z1),        # outer rail
        box(-46, 12, *by(21.0, 26.0), z0, z1),        # inner rail
        box(-50, -44, *by(21.0, 39.3), z0, z1),       # rear bar
        box(9, 16, *by(21.0, 39.3), z0, z1),          # front bar
        box(-42, -30, *by(24.0, 34.0), z0, z1),       # web under the rear post
        box(-2, 10, *by(24.0, 34.0), z0, z1),         # web under the front post
        box(12.5, 16, *by(21.0, 39.3), PCB_Z + PCB_T + 3, z1),   # front face down to the board
        box(-50, -46.5, *by(21.0, 39.3), AXLE_Z + 4, z1),        # rear lip over the motor end
    ]
    b = parts[0]
    for p in parts[1:]:
        b = b.union(p)
    for x in (-36, 4):
        post = cyl_z(4.8, z1, z1 + 12, x, s * 29.5)
        b = b.union(post).cut(cyl_z(1.8, z1 + 3, z1 + 13, x, s * 29.5))
    # clip around the motor end, with a foot for the bolt
    b = b.union(box(-50, -44, *by(39.3, 42.0), TOP, z1))
    foot = box(-52, -42, *by(39.5, 48.0), TOP, TOP + 3.0).edges("|Z").fillet(1.5)
    b = b.union(foot)
    # front feet with bolts beside the STM32 board
    b = b.union(box(14, 21, *by(18.5, 25.5), TOP, TOP + 3.0))
    return b


def nut_bolt(x, y, z):
    nut = cq.Workplane("XY").polygon(6, 6.4).extrude(2.6).translate((x, y, z))
    washer = cyl_z(3.6, z - 0.6, z, x, y)
    rod = cyl_z(1.5, z + 2.6, z + 6.0, x, y)
    return nut.union(washer).union(rod)


def bolts():
    s = None
    for side in (1, -1):
        for (x, y, z) in ((-47, side * 44.5, TOP + 3.0), (17.5, side * 22, TOP + 3.0), (24.5, side * 36, TOP + 0.6)):
            b = nut_bolt(x, y, z)
            s = b if s is None else s.union(b)
    return s


def skid():
    return box(-72, -54, -11, 11, 1.0, PCB_Z).edges("|Y").fillet(5).edges("|X").fillet(3)


# ---------------------------------------------------------------- ribbon cables
def ribbon(side):
    yc = side * 30.1
    pts = [(-54.5, yc, AXLE_Z + 10), (-61, yc * 0.85, AXLE_Z + 17), (-69, yc * 0.45, AXLE_Z + 13),
           (-73, side * 4, AXLE_Z + 4), (-70, -side * 3, TOP + 6)]
    path = cq.Workplane("XY").spline([cq.Vector(*p) for p in pts], includeCurrent=False)
    v0, v1 = cq.Vector(*pts[0]), cq.Vector(*pts[1])
    t = (v1 - v0).normalized()
    plane = cq.Plane(origin=v0, xDir=cq.Vector(0, 1, 0).cross(t).normalized() if abs(t.y) < 0.9 else cq.Vector(1, 0, 0), normal=t)
    return cq.Workplane(plane).rect(0.6, 5.5).sweep(path, transition="round")


def connector():
    return box(-73, -66, -12, 12, TOP, TOP + 5.5)


# ---------------------------------------------------------------- assembly
def build():
    a = cq.Assembly(name="micromouse")
    a.add(main_pcb(), name="main_pcb", color=C["pcb"])
    a.add(aux_header_pads(), name="front_aux_header_pads", color=C["gold"])
    a.add(sensor_pcb(), name="sensor_pcb", color=C["pcb"])
    sp, pins = sensor_header()
    a.add(sp, name="sensor_header", color=C["black"])
    a.add(pins, name="sensor_header_pins", color=C["gold"])
    a.add(sensor_pads(), name="sensor_pads", color=C["gold"])
    for side, nm in ((1, "left"), (-1, "right")):
        a.add(place_wheel(tyre(), side), name=f"tyre_{nm}", color=C["tyre"])
        a.add(place_wheel(rim(), side), name=f"rim_{nm}", color=C["rim"])
        a.add(motor(side), name=f"tt_motor_{nm}", color=C["black"])
        b, cap = encoder(side)
        a.add(b, name=f"encoder_board_{nm}", color=C["pcb_dark"])
        a.add(cap, name=f"encoder_cap_{nm}", color=C["black"])
        a.add(bracket(side), name=f"motor_bracket_{nm}", color=C["yellow"])
        sb, sc, sh = tof_board_side(side)
        a.add(sb, name=f"tof_board_{nm}", color=C["pcb"])
        a.add(sc, name=f"tof_sensor_{nm}", color=C["chip"])
        a.add(sh, name=f"tof_header_{nm}", color=C["black"])
        try:
            a.add(ribbon(side), name=f"ribbon_{nm}", color=C["white"])
        except Exception as e:
            print("ribbon skipped:", e)
    a.add(bolts(), name="bolts", color=C["metal"])
    fb, fc, fh = tof_board_front()
    a.add(fb, name="tof_board_front", color=C["pcb"])
    a.add(fc, name="tof_sensor_front", color=C["chip"])
    a.add(fh, name="tof_header_front", color=C["black"])
    a.add(socket_4pin(), name="socket_4pin", color=C["black"])
    board, qfp, legs, usb, stack, sock, parts, bb, bc, pads = processor()
    a.add(board, name="stm32_board", color=C["pcb"])
    a.add(legs, name="stm32_chip_legs", color=C["metal"])
    a.add(qfp, name="stm32_chip", color=C["chip"])
    a.add(usb, name="micro_usb", color=C["metal"])
    a.add(stack, name="stacking_headers", color=C["black"])
    a.add(sock, name="stm32_socket", color=C["black"])
    a.add(parts, name="smd_parts", color=C["chip"])
    a.add(bb, name="buttons", color=C["metal"])
    a.add(bc, name="button_caps", color=C["white"])
    a.add(pads, name="stm32_pads", color=C["gold"])
    a.add(battery(), name="battery", color=C["orange"])
    a.add(skid(), name="rear_skid", color=C["yellow"])
    a.add(connector(), name="encoder_connector", color=C["white"])
    return a


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    a = build()
    a.export(f"{out}/micromouse.step")
    a.export(f"{out}/micromouse.glb", tolerance=0.05, angularTolerance=0.15)
    print("saved")
