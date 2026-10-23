# -*- coding: utf-8 -*-
"""R3 页：正上方多距离测试示意（同一只卡通箱 + 5 个天线高度）。

画面：箱体前壁剖开，能看到内部 6 台金属背板整机；天线在箱顶正上方
0 / 10 / 20 / 30 / 40 cm 五个位置（半透明），左侧一条距离标尺。

输出：_3d_out2/R3_scan.png（透明底，1100×1600）
用法：blender -b -P rfid3d_r3.py
"""
import bpy, math, os
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "_3d_out2")
os.makedirs(OUT, exist_ok=True)

BW, BD, BH = 0.40, 0.30, 0.32   # 600×400×300，300 立起
CARD = (0.62, 0.47, 0.31)
DARK = (0.10, 0.11, 0.12)
METAL = (0.62, 0.64, 0.67)
WHITE = (0.86, 0.865, 0.87)
ACCENT = (0.24, 0.36, 0.62)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def cube(name, dims, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        bpy.context.view_layer.objects.active = o
        m = o.modifiers.new("bev", 'BEVEL')
        m.width = bevel
        m.segments = 2
    return o


def cyl(name, r, depth, loc, rot, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    return o


def build_scene():
    m_card = mat("card", CARD, 0.85)
    m_inner = mat("inner", (0.50, 0.38, 0.26), 0.9)
    m_dark = mat("dark", DARK, 0.55)
    m_metal = mat("metal", METAL, 0.32, 0.85)
    m_white = mat("white", WHITE, 0.5)
    m_ghost = mat("ghost", (0.20, 0.30, 0.55), 0.5, 0.0, 0.65)
    m_line = mat("line", ACCENT, 0.4)

    t = 0.010
    # 箱体：底 + 后 + 左 + 右 + 顶（前面剖开）
    cube("bottom", (BW, BD, t), (0, 0, t / 2), m_card)
    cube("back", (BW, t, BH), (0, BD / 2 - t / 2, BH / 2), m_card)
    cube("left", (t, BD, BH), (-BW / 2 + t / 2, 0, BH / 2), m_card)
    cube("right", (t, BD, BH), (BW / 2 - t / 2, 0, BH / 2), m_card)
    cube("top", (BW, BD, t), (0, 0, BH - t / 2), m_card)
    # 内壁（深一点，剖开后有层次）
    cube("inner_back", (BW - 2 * t, 0.002, BH - 2 * t), (0, BD / 2 - t - 0.001, BH / 2), m_inner)

    # 6 个竖立的平板包装盒（2 列 × 3 排，像 iPad 盒插在箱里）
    m_box = mat("box", (0.88, 0.875, 0.86), 0.75)
    m_lid = mat("lid", (0.73, 0.72, 0.70), 0.7)
    m_lab = mat("lab", (0.32, 0.40, 0.58), 0.6)
    BWX, BTH, BHX = 0.185, 0.032, 0.270
    for col, x in enumerate((-0.095, 0.095)):
        for row, y in enumerate((-0.085, -0.045, -0.005)):
            i = col * 3 + row
            z = 0.012 + BHX / 2
            cube(f"pkg{i}", (BWX, BTH, BHX), (x, y, z), m_box, bevel=0.002)
            # 盒盖分缝（靠近顶部的一圈）
            cube(f"pkg{i}_lid", (BWX + 0.002, BTH + 0.002, 0.006), (x, y, z + BHX * 0.32), m_lid, bevel=0.001)
            # 正面标签
            cube(f"pkg{i}_lab", (0.090, 0.002, 0.030), (x, y - BTH / 2 - 0.001, z), m_lab)

    # 5 个天线高度：贴住 / 10 / 20 / 30 / 40 cm
    gaps = [0.004, 0.10, 0.20, 0.30, 0.40]
    zs = []
    for i, g in enumerate(gaps):
        z = BH + g + 0.006
        zs.append(z)
        # 线框方框表示该高度的天线（避免半透明面片叠成一根柱子）
        A, th = 0.259, 0.010
        for sx in (-1, 1):
            cube(f"ant{i}_x{sx}", (A, 0.012, th), (0, sx * A / 2, z), m_ghost)
            cube(f"ant{i}_y{sx}", (th, A, 0.012), (sx * A / 2, 0, z), m_ghost)
        cube(f"ant{i}_n", (0.020, 0.020, 0.020), (0, 0, z + 0.006), m_ghost)

    # 距离标尺
    x0 = -BW / 2 - 0.075
    cyl("axis", 0.0022, zs[-1] - BH + 0.01, (x0, 0.02, (BH + zs[-1]) / 2), (0, 0, 0), m_line)
    for z in zs:
        cyl(f"tick{z:.3f}", 0.0022, 0.030, (x0 + 0.015, 0.02, z), (0, 0, math.pi / 2), m_line)
    cyl("base_tick", 0.0022, 0.030, (x0 + 0.015, 0.02, BH), (0, 0, math.pi / 2), m_line)


def setup(target=(0, 0, 0.33), ortho=0.86, direction=(-0.62, -1.0, 0.34), res=(1100, 1600)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = 0.15

    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 1.0

    bpy.ops.object.light_add(type='SUN', location=(1.5, -2.2, 2.6))
    sun = bpy.context.active_object
    sun.data.energy = 2.4
    sun.data.angle = math.radians(9)
    sun.rotation_euler = (math.radians(48), math.radians(4), math.radians(28))

    bpy.ops.object.light_add(type='AREA', location=(-1.4, -1.1, 1.0))
    ar = bpy.context.active_object
    ar.data.energy = 24
    ar.data.size = 2.4
    ar.rotation_euler = (math.radians(62), 0, math.radians(-48))

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    d = Vector(direction).normalized()
    tgt = Vector(target)
    cam.location = tgt + d * 3.0
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam


def main():
    reset()
    build_scene()
    setup()
    bpy.context.scene.render.filepath = os.path.join(OUT, "R3_scan.png")
    bpy.ops.render.render(write_still=True)
    print("[render] R3_scan", flush=True)


if __name__ == "__main__":
    main()
