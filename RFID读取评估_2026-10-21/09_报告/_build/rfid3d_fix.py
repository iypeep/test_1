# -*- coding: utf-8 -*-
"""Blender 4.3 后台渲染 · 六种放置方式（修正版）

修正点（按现场反馈）：
  1) 箱体在产线上是**立起来**的：立起 600，着地面 400×300；
     防爆标签在**最大的面**（600×400 = F-FRONT），条码+6 序列号在对应的 F-BACK；
     封箱带在 400×300 的 T-TOP / B-BOTTOM。
  2) 旧版把 600×400 当底面，A1 画成"趴着"，且 A5/A6 读码器与箱体穿模。
     新版每个姿态按箱体竖直半高 + 9 cm 间隙重新摆读码器。

坐标：X = 宽 0.40，Y = 深 0.30，Z = 立起高 0.60（单位 m）
输出：_3d_out2/A1_bottom_down.png … A6_right_down.png
用法：blender -b -P rfid3d_fix.py            # 全部
      ONLY=A1 blender -b -P rfid3d_fix.py     # 单张
"""
import bpy, math, os, time
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "_3d_out2")
LBL = os.path.join(_HERE, "_3d_labels")
os.makedirs(OUT, exist_ok=True)

BW, BD, BH = 0.40, 0.30, 0.60          # 宽 × 深 × 立起高
CARD = (0.62, 0.45, 0.28)
ACCENT = (0.16, 0.30, 0.62)
SAMPLES = 32
RES = (1024, 768)
GAP = 0.008                             # 箱底到天线面（10-19 测试：箱体直接放在读码器上）
FACE_OFF = 0.125 * 1.30                 # 读码器天线面在局部 +Y 的偏移（含 1.30 放大）


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


def cube(name, dims, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new("bev", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    return o


def plane(name, size, loc, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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
    body = cube("box", (BW, BD, BH), (0, 0, 0), m_card, bevel=0.004)
    parent(body, rig)

    # 封箱带：上面 + 下面（400×300 面），两道沿 Y + 一道沿 X
    for sign in (1, -1):
        z = sign * (BH / 2 + 0.002)
        for sx in (-0.09, 0.09):
            t = cube(f"tape_y{sign}{sx}", (0.05, BD * 0.999, 0.0035), (sx, 0, z), m_tape)
            parent(t, rig)
        t = cube(f"tape_x{sign}", (BW * 0.999, 0.05, 0.0035), (0, 0, sign * (BH / 2 + 0.004)), m_tape)
        parent(t, rig)

    nx, ny, nz = BW / 2 + 0.0012, BD / 2 + 0.0012, BH / 2 + 0.0012
    rx = (math.pi / 2, 0, 0)

    # 正面（-Y，600×400）：防爆标识
    f = plane("label_front", (0.20, 0.145), (0.0, -ny, 0.12), rx,
              mat_image("m_front", "label_front.png"))
    parent(f, rig)
    # 背面（+Y，600×400）：条码 + 6 DSN
    b = plane("label_back", (0.26, 0.179), (0.0, ny, 0.10), (math.pi / 2, 0, math.pi),
              mat_image("m_back", "label_back.png"))
    parent(b, rig)

    faces = {
        "F-FRONT": ((-0.10, -ny, -0.20), rx),
        "F-BACK": ((0.10, ny, -0.20), (math.pi / 2, 0, math.pi)),
        "S-LEFT": ((-nx, 0.0, -0.20), (math.pi / 2, 0, -math.pi / 2)),
        "S-RIGHT": ((nx, 0.0, -0.20), (math.pi / 2, 0, math.pi / 2)),
        "T-TOP": ((0.0, 0.06, nz), (0, 0, 0)),
        "B-BOTTOM": ((0.0, 0.06, -nz), (math.pi, 0, 0)),
    }
    for k, (loc, rot) in faces.items():
        p = plane(f"tag_{k}", (0.105, 0.0375), loc, rot, mat_image(f"m_{k}", f"tag_{k}.png"))
        parent(p, rig)
    return rig


# ------------------------------------------------------------------ 读码器
def build_reader(vendor="A", gain=6):
    """天线辐射面朝 +Y（局部坐标）"""
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
    body = cube("reader_body", (hw, hh, hd), (0, 0, 0), m_body, bevel=0.005)
    parent(body, rig)
    fr = cube("reader_face", (hw * 0.94, hh * 0.94, 0.006), (0, hd / 2 + 0.002, 0), m_body)
    parent(fr, rig)
    for i in range(4):
        x = (i - 1.5) * (hw * 0.20)
        c = cube(f"conn{i}", (0.011, 0.011, 0.014), (x, hd / 2 + 0.010, -hh * 0.30), m_metal)
        parent(c, rig)
    led = cube("led", (0.018, 0.005, 0.005), (hw * 0.36, hd / 2 + 0.005, hh * 0.22), m_led)
    parent(led, rig)

    aw = 0.259 if gain == 6 else 0.360
    ad = 0.038 if gain == 6 else 0.035
    ant = cube("antenna", (aw, ad, aw), (0, hd / 2 + 0.004 + ad / 2, 0), m_ant, bevel=0.004)
    parent(ant, rig)
    rim = cube("antenna_rim", (aw * 1.02, ad * 0.22, aw * 1.02),
               (0, hd / 2 + 0.004 + ad * 0.88, 0), m_body)
    parent(rim, rig)
    rig.scale = (1.30, 1.30, 1.30)
    return rig


# ------------------------------------------------------------------ 场景
def setup_scene(cam_dir, target=(0, 0, -0.18), ortho=1.34, dist=4.0):
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

    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.86, 0.875, 0.90, 1)
    bg.inputs["Strength"].default_value = 0.85

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
    print(f"[render] {name}", flush=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))


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


def dim_line(p_from, p_to, radius=0.0035):
    v = Vector(p_to) - Vector(p_from)
    mid = (Vector(p_from) + Vector(p_to)) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=v.length, location=mid)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = v.to_track_quat('Z', 'Y')
    o.data.materials.append(mat_solid("dim", ACCENT, rough=0.4))
    return o


# ------------------------------------------------------------------ 六种放置
UP = (math.pi / 2, 0, 0)          # 天线面 +Y → +Z
# (名字, 箱体欧拉角, 箱体竖直半高)
POSES = [
    ("A1_bottom_down", (0, 0, 0), 0.30),
    ("A2_top_down", (math.pi, 0, 0), 0.30),
    ("A3_front_down", (math.pi / 2, 0, 0), 0.15),
    ("A4_back_down", (-math.pi / 2, 0, 0), 0.15),
    ("A5_left_down", (0, -math.pi / 2, 0), 0.20),
    ("A6_right_down", (0, math.pi / 2, 0), 0.20),
]

ONLY = os.environ.get("ONLY", "")
for name, rbox, half in POSES:
    if ONLY and ONLY not in name:
        continue
    reset()
    carton = build_carton()
    carton.rotation_euler = rbox
    reader = build_reader("A", 6)
    reader.location = (0, 0, -(half + GAP + FACE_OFF))
    reader.rotation_euler = UP
    bpy.context.view_layer.update()

    setup_scene((-0.85, -1.0, 0.55), target=(0, 0, -0.18), ortho=1.34, dist=4.0)
    render(name)

# ------------------------------------------------------------------ 距离几何（上/下/侧，10 cm）
DIST = 0.10
DCFG = [
    ("D_up", (0, 0, BH / 2 + DIST + FACE_OFF), (-math.pi / 2, 0, 0), (0, 0, 0.18), 1.58),
    ("D_down", (0, 0, -(BH / 2 + DIST + FACE_OFF)), (math.pi / 2, 0, 0), (0, 0, -0.18), 1.58),
    ("D_side", (0, -(BD / 2 + DIST + FACE_OFF), 0.0), (0, 0, 0), (0, -0.12, 0.0), 1.58),
]
for name, rpos, rrot, tgt, osc in DCFG:
    reset()
    build_carton()
    reader = build_reader("A", 6)
    reader.location = rpos
    reader.rotation_euler = rrot
    if name == "D_up":
        dim_line((0.10, 0, BH / 2), (0.10, 0, BH / 2 + DIST))
    elif name == "D_down":
        dim_line((0.10, 0, -BH / 2), (0.10, 0, -(BH / 2 + DIST)))
    else:
        dim_line((-0.16, -BD / 2, 0.0), (-0.16, -(BD / 2 + DIST), 0.0))
    setup_scene((-0.95, -1.05, 0.30), target=tgt, ortho=osc, dist=3.6)
    render(name)


# ------------------------------------------------------------------ 一台箱体 + 三副天线（同框）
def antenna_unit(aw=0.259, ad=0.038):
    """单副板状天线：白色面罩 + 深色背框 + N 接头，辐射面朝 +Y。"""
    m_face = mat_solid("antface", (0.90, 0.905, 0.91), rough=0.45)
    m_frame = mat_solid("antframe", (0.055, 0.058, 0.065), rough=0.5, metal=0.2)
    m_metal = mat_solid("antmetal", (0.55, 0.56, 0.58), rough=0.3, metal=0.9)
    rig = empty("ANT")
    face = cube("ant_face", (aw, ad, aw), (0, 0, 0), m_face, bevel=0.004)
    parent(face, rig)
    frame = cube("ant_frame", (aw * 0.86, ad * 0.55, aw * 0.86), (0, -ad * 0.62, 0), m_frame, bevel=0.003)
    parent(frame, rig)
    n = cube("ant_n", (0.016, 0.018, 0.016), (0, -ad * 0.95, 0), m_metal)
    parent(n, rig)
    return rig


reset()
build_carton()
GAP3 = 0.008
A_TH = 0.038
a_bottom = antenna_unit()
a_bottom.location = (0, 0, -(BH / 2 + GAP3 + A_TH / 2))
a_bottom.rotation_euler = (math.pi / 2, 0, 0)          # +Y → +Z

a_top = antenna_unit()
a_top.location = (0, 0, BH / 2 + GAP3 + A_TH / 2)
a_top.rotation_euler = (-math.pi / 2, 0, 0)            # +Y → -Z

a_side = antenna_unit()
a_side.location = (-(BW / 2 + GAP3 + A_TH / 2), 0, 0.02)
a_side.rotation_euler = (0, 0, -math.pi / 2)           # +Y → +X

setup_scene((-0.78, -1.0, 0.42), target=(0, 0, -0.02), ortho=1.16, dist=4.0)
bpy.context.scene.render.film_transparent = True
bpy.context.scene.render.resolution_x = 2048
bpy.context.scene.render.resolution_y = 1536
render("THREE_readers")

print("ALL DONE", flush=True)
