# -*- coding: utf-8 -*-
"""Blender 4.3 后台渲染：卡通箱 6 种放置方式 / 距离几何 / 读码器与天线圈
坐标：X = 长(0.60)  Y = 宽(0.40)  Z = 高(0.30)，单位 m
FRONT 面在 -Y，BACK 面在 +Y，TOP 在 +Z，BOTTOM 在 -Z
"""
import bpy, math, os, time
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "_3d_out")
LBL = os.path.join(_HERE, "_3d_labels")
os.makedirs(OUT, exist_ok=True)

L, Wd, H = 0.60, 0.40, 0.30          # 箱体 长 × 宽 × 高
CARD = (0.62, 0.45, 0.28)            # 瓦楞纸色
ACCENT = (0.16, 0.30, 0.62)
SAMPLES = 32
RES = (1024, 768)


# ------------------------------------------------------------------ 基础工具
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat_solid(name, color, rough=0.75, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def mat_image(name, fname, rough=0.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(LBL, fname))
    tex.interpolation = 'Cubic'
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m


def apply_scale(o):
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def cube(name, dims, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    apply_scale(o)
    o.data.materials.append(mat)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL')
        md.width = bevel
        md.segments = 3
    return o


def plane(name, size, loc, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], 1.0)
    apply_scale(o)
    o.data.materials.append(mat)
    return o


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    return e


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


# ------------------------------------------------------------------ 箱体
def build_carton():
    m_card = mat_solid("cardboard", CARD, rough=0.85)
    m_tape = mat_solid("tape", (0.86, 0.86, 0.83), rough=0.35)

    rig = empty("CARTON")

    body = cube("box", (L, Wd, H), (0, 0, 0), m_card, bevel=0.004)
    parent(body, rig)

    # 封箱带（顶面两道 + 一道横跨）
    for y in (-0.10, 0.10):
        t = cube(f"tape_y{y}", (L * 0.999, 0.055, 0.0035), (0, y, H / 2 + 0.002), m_tape)
        parent(t, rig)
    t = cube("tape_x", (0.055, Wd * 0.999, 0.0035), (0, 0, H / 2 + 0.0035), m_tape)
    parent(t, rig)
    # 底面封箱带
    t = cube("tape_b", (0.055, Wd * 0.999, 0.0035), (0, 0, -H / 2 - 0.002), m_tape)
    parent(t, rig)

    nx = L / 2 + 0.0012
    ny = Wd / 2 + 0.0012
    nz = H / 2 + 0.0012
    rx = (math.pi / 2, 0, 0)
    ry = (math.pi / 2, 0, math.pi / 2)

    # 正面（-Y）：防爆标识
    f = plane("label_front", (0.19, 0.138), (0.17, -ny, 0.05), rx, mat_image("m_front", "label_front.png"))
    parent(f, rig)
    # 背面（+Y）：条码 + 6 DSN
    b = plane("label_back", (0.26, 0.179), (-0.14, ny, 0.01), (math.pi / 2, 0, math.pi),
              mat_image("m_back", "label_back.png"))
    parent(b, rig)

    # 面标
    faces = {
        "F-FRONT": ((-0.24, -ny, -0.10), rx),
        "F-BACK": ((0.20, ny, -0.10), (math.pi / 2, 0, math.pi)),
        "S-LEFT": ((-nx, 0.09, -0.09), (math.pi / 2, 0, -math.pi / 2)),
        "S-RIGHT": ((nx, 0.09, -0.09), (math.pi / 2, 0, math.pi / 2)),
        "T-TOP": ((0.20, 0.0, nz), (0, 0, 0)),
        "B-BOTTOM": ((0.20, 0.0, -nz), (math.pi, 0, 0)),
    }
    for k, (loc, rot) in faces.items():
        p = plane(f"tag_{k}", (0.105, 0.0375), loc, rot, mat_image(f"m_{k}", f"tag_{k}.png"))
        parent(p, rig)
    return rig


# ------------------------------------------------------------------ 读码器 + 天线
def build_reader(vendor="A", gain=6):
    """天线辐射面朝 +Y（assembly 局部坐标）。vendor A = Impinj 体系 4 口，B = 国产方案"""
    if vendor == "A":
        hw, hd, hh = 0.240, 0.150, 0.055
        m_body = mat_solid("rdA", (0.055, 0.058, 0.065), rough=0.42, metal=0.35)
    else:
        hw, hd, hh = 0.200, 0.130, 0.048
        m_body = mat_solid("rdB", (0.13, 0.145, 0.17), rough=0.5, metal=0.20)
    m_ant = mat_solid("ant", (0.90, 0.905, 0.90), rough=0.42)
    m_metal = mat_solid("metal", (0.60, 0.61, 0.63), rough=0.3, metal=0.9)
    m_led = mat_solid("led", (0.10, 0.70, 0.30), rough=0.25)

    rig = empty("READER")

    # 外壳
    body = cube("reader_body", (hw, hh, hd), (0, 0, 0), m_body, bevel=0.005)
    parent(body, rig)
    # 前面板（贴天线那一侧）+ 4 个天线口 + 指示灯
    fr = cube("reader_face", (hw * 0.94, hh * 0.94, 0.006), (0, hd / 2 + 0.002, 0), m_body)
    parent(fr, rig)
    for i in range(4):
        x = (i - 1.5) * (hw * 0.20)
        c = cube(f"conn{i}", (0.011, 0.011, 0.014), (x, hd / 2 + 0.010, -hh * 0.30), m_metal)
        parent(c, rig)
    led = cube("led", (0.018, 0.005, 0.005), (hw * 0.36, hd / 2 + 0.005, hh * 0.22), m_led)
    parent(led, rig)

    # 板状天线（口径随增益变化），辐射面朝 +Y
    aw = 0.259 if gain == 6 else 0.360
    ad = 0.038 if gain == 6 else 0.035
    ant = cube("antenna", (aw, ad, aw), (0, hd / 2 + 0.012 + ad / 2, 0), m_ant, bevel=0.004)
    parent(ant, rig)
    rim = cube("antenna_rim", (aw * 1.02, ad * 0.22, aw * 1.02),
               (0, hd / 2 + 0.012 + ad * 0.88, 0), m_body)
    parent(rim, rig)
    # 后侧支架（可上抱杆）
    br = cube("bracket", (hw * 0.08, 0.055, hw * 0.08), (0, -hd / 2 - 0.030, 0), m_metal)
    parent(br, rig)
    rig.scale = (1.30, 1.30, 1.30)      # 示意放大，便于在小图里看清结构
    return rig


def m_solid_light():
    return mat_solid("x", (1, 1, 1))


# ------------------------------------------------------------------ 场景
FLOOR_Z = -1.20
FLOOR_OFF = [False]


def setup_scene(cam_dir, target=(0, 0, -0.02), ortho=1.45, dist=4.0, floor=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = 0.55

    # 世界：浅灰
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.86, 0.875, 0.90, 1)
    bg.inputs["Strength"].default_value = 0.85

    # 地面
    if not floor:
        FLOOR_OFF[0] = True
    m_fl = mat_solid("floor", (0.80, 0.81, 0.82), rough=0.92)
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, FLOOR_Z))
        fl = bpy.context.active_object
        fl.data.materials.append(m_fl)

    # 灯
    bpy.ops.object.light_add(type='SUN', location=(2, -3, 4))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(50), math.radians(8), math.radians(35))

    bpy.ops.object.light_add(type='AREA', location=(-2.2, -1.6, 1.6))
    ar = bpy.context.active_object
    ar.data.energy = 45
    ar.data.size = 2.5
    ar.rotation_euler = (math.radians(62), 0, math.radians(-52))

    # 相机
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho
    cam_data.clip_start = 0.05
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    d = Vector(cam_dir).normalized()
    tgt = Vector(target)
    cam.location = tgt + d * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    return cam


def render(name):
    bpy.context.scene.render.filepath = os.path.join(OUT, name)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[render] {name} {time.time()-t0:.1f}s")


def dim_line(p_from, p_to, radius=0.0035):
    v = Vector(p_to) - Vector(p_from)
    mid = (Vector(p_from) + Vector(p_to)) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=v.length, location=mid)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = v.to_track_quat('Z', 'Y')
    o.data.materials.append(mat_solid("dim", ACCENT, rough=0.4))
    return o




def add_beam(face_pt, direction, length, r1=0.20, r2=0.075, color=ACCENT):
    d = Vector(direction).normalized()
    mid = Vector(face_pt) + d * (length / 2)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r1, radius2=r2, depth=length, location=mid)
    o = bpy.context.active_object
    o.name = "beam"
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    m = bpy.data.materials.new("beam")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Alpha"].default_value = 0.16
    o.data.materials.append(m)
    return o


# ------------------------------------------------------------------ 6 种放置
# (名字, 箱体欧拉角, 读码器位置, 读码器欧拉角, 相机方向, 说明)
UP = (math.pi / 2, 0, 0)        # 天线面 +Y → +Z（朝上）
DOWN = (-math.pi / 2, 0, 0)     # 天线面 +Y → -Z（朝下）
POSES = [
    ("A1_upright_bottom", (0, 0, 0), (0, 0, -0.40), UP, (-0.95, -0.85, -0.72), 1.26),
    ("A2_upright_front",  (0, 0, 0), (0, -0.52, 0.00), (0, 0, 0), (0.80, -1.10, 0.34), 1.30),
    ("A3_upright_back",   (0, 0, 0), (0, 0.52, 0.00), (0, 0, math.pi), (0.80, 1.10, 0.34), 1.30),
    ("A4_lying_front",    (math.pi / 2, 0, 0), (0, 0, -0.34), UP, (-0.95, -0.62, -0.95), 1.26),
    ("A5_lying_back",     (-math.pi / 2, 0, 0), (0, 0, -0.34), UP, (-0.95, 0.62, -0.95), 1.26),
    ("A6_inverted_top",   (math.pi, 0, 0), (0, 0, -0.40), UP, (-0.95, -0.60, -0.95), 1.26),
]

ONLY = os.environ.get("ONLY", "")
for name, rbox, rpos, rrot, camdir, oscale in POSES:
    if ONLY and ONLY not in name:
        continue
    reset()
    carton = build_carton()
    carton.rotation_euler = rbox
    reader = build_reader("A", 6)
    reader.location = rpos
    reader.rotation_euler = rrot
    bpy.context.view_layer.update()
    face = reader.matrix_world @ Vector((0, 0.125 * 1.30, 0))
    if abs(rrot[0]) > 0.5:                      # 朝上/朝下
        dz = (H / 2 if rrot[0] > 0 else -H / 2) - face.z
        add_beam(face, (0, 0, 1 if rrot[0] > 0 else -1), abs(dz) - 0.005)
    else:                                       # 侧向
        dy = (0 if abs(rrot[2]) > 2 else 1) * (-1 if abs(rrot[2]) < 1 else 1)
        surf = (-Wd / 2 if dy > 0 else Wd / 2)
        add_beam(face, (0, dy, 0), abs(surf - face.y) - 0.005)
    # 读码器到箱体中心的测距线
    tgt = (0, 0, -0.09) if rpos[2] < 0 else (0, rpos[1] * 0.34, 0.00)
    setup_scene(camdir, target=tgt, ortho=oscale, dist=3.2, floor=False)
    render(name)
    print("done", name, flush=True)

# ------------------------------------------------------------------ 距离几何（上/下/侧，10 cm）
DIST = 0.10
DCFG = [
    ("D_up",   (0, 0, H / 2 + DIST + 0.075), (-math.pi / 2, 0, 0)),
    ("D_down", (0, 0, -(H / 2 + DIST + 0.075)), (math.pi / 2, 0, 0)),
    ("D_side", (0, -(Wd / 2 + DIST + 0.075), 0.0), (0, 0, 0)),
]
for name, rpos, rrot in DCFG:
    reset()
    build_carton()
    reader = build_reader("A", 6)
    reader.location = rpos
    reader.rotation_euler = rrot
    if name == "D_up":
        dim_line((0.10, 0, H / 2), (0.10, 0, rpos[2] - 0.10))
    elif name == "D_down":
        dim_line((0.10, 0, -H / 2), (0.10, 0, rpos[2] + 0.10))
    else:
        dim_line((-0.16, -Wd / 2, 0.0), (-0.16, rpos[1] + 0.11, 0.0))
    setup_scene((-1.05, -1.10, 0.26), target=(0, 0, -0.02), ortho=1.20, dist=3.2, floor=True)
    render(name)

# ------------------------------------------------------------------ 读码器 / 天线阵容
CFG = [("R_A6", "A", 6), ("R_A9", "A", 9), ("R_B6", "B", 6), ("R_B9", "B", 9)]
for name, vendor, gain in CFG:
    reset()
    r = build_reader(vendor, gain)
    r.location = (0, 0, 0.06)
    r.rotation_euler = (0, 0, math.radians(-32))
    setup_scene((-0.95, -1.15, 0.30), target=(0, 0, 0.03), ortho=0.82, dist=3.0, floor=True)
    render(name)
print("ALL DONE")
