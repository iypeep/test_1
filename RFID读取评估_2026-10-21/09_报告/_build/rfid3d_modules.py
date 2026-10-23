# -*- coding: utf-8 -*-
"""P5 顶排缺图型号的 Blender 建模渲染（R700 / R420 / FX9600 / M6e）。

尺寸取手册（mm→m）：
  R700    214 × 149 × 30，4 个 N 型天线口 + RJ45 + DC + 2 LED
  R420    190 × 127 × 33，4 口
  FX9600  273 × 184 × 51，8 口 + 安装法兰
  M6e      66 ×  36 ×  8，PCB + 屏蔽罩 + 4×U.FL + 排针

输出：_3d_out2/MOD_R700.png 等（透明底，便于和原厂白底图混排）
用法：blender -b -P rfid3d_modules.py
"""
import bpy, math, os
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "_3d_out2")
os.makedirs(OUT, exist_ok=True)

BODY = (0.038, 0.040, 0.045)
EDGE = (0.020, 0.022, 0.026)
PANEL = (0.780, 0.785, 0.790)
METAL = (0.560, 0.570, 0.585)
PCB = (0.030, 0.135, 0.075)
SHIELD = (0.520, 0.535, 0.550)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
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
        m.segments = 3
    return o


def cyl(name, radius, depth, loc, rot, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    return o


# ------------------------------------------------------------------ 整机
def build_reader(name, w, d, h, ports, flange=False):
    m_body = mat("body", BODY, 0.45, 0.25)
    m_edge = mat("edge", EDGE, 0.5, 0.2)
    m_panel = mat("panel", PANEL, 0.55)
    m_metal = mat("metal", METAL, 0.30, 0.9)
    m_dark = mat("dark", (0.055, 0.060, 0.068), 0.6)

    cube(f"{name}_body", (w, d, h), (0, 0, 0), m_body, bevel=min(w, d) * 0.035)
    # 顶面浅色面板（标签位）
    cube(f"{name}_panel", (w * 0.40, d * 0.26, 0.0015), (-w * 0.16, d * 0.16, h / 2 + 0.001), m_panel)
    # 散热槽
    for i in range(7):
        yy = d * (-0.34 + i * 0.085)
        cube(f"{name}_slot{i}", (w * 0.30, 0.0024, 0.0012), (w * 0.20, yy, h / 2 + 0.0022), m_edge)

    # 天线口（前缘，沿 -Y 伸出）
    step = w / (ports + 1)
    for i in range(ports):
        x = -w / 2 + step * (i + 1)
        cyl(f"{name}_port{i}", 0.0060, 0.014, (x, -d / 2 - 0.006, h * 0.10),
            (math.pi / 2, 0, 0), m_metal)
        cyl(f"{name}_pin{i}", 0.0022, 0.015, (x, -d / 2 - 0.0065, h * 0.10),
            (math.pi / 2, 0, 0), m_dark)

    # RJ45 / DC / LED
    cube(f"{name}_rj45", (0.016, 0.012, 0.010), (w * 0.20, -d / 2 + 0.006, h * 0.28), m_dark)
    cyl(f"{name}_dc", 0.0045, 0.012, (w * 0.30, -d / 2 + 0.006, h * 0.28),
        (math.pi / 2, 0, 0), m_dark)
    for i, col in enumerate(((0.10, 0.70, 0.30), (0.95, 0.70, 0.15))):
        m = mat(f"led{i}", col, 0.3)
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (*col, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
        cyl(f"{name}_led{i}", 0.0018, 0.0012, (-w * 0.36 + i * 0.010, d * 0.28, h / 2 + 0.002),
            (0, 0, 0), m)

    if flange:
        cube(f"{name}_flange", (w * 1.14, d * 1.06, h * 0.16), (0, 0, -h * 0.42), m_edge, bevel=0.003)


def build_module(name, w, d, h):
    m_pcb = mat("pcb", PCB, 0.6)
    m_shield = mat("shield", SHIELD, 0.35, 0.6)
    m_dark = mat("dark", (0.06, 0.065, 0.07), 0.6)
    m_metal = mat("metal", METAL, 0.3, 0.9)

    cube(f"{name}_pcb", (w, d, h), (0, 0, 0), m_pcb, bevel=0.001)
    cube(f"{name}_shield", (w * 0.58, d * 0.66, h * 0.45), (0, d * 0.08, h / 2), m_shield, bevel=0.0015)
    # U.FL
    for i in range(4):
        x = -w / 2 + w * (i + 1) / 5
        cyl(f"{name}_ufl{i}", 0.0022, 0.0022, (x, -d * 0.36, h / 2 + 0.001), (0, 0, 0), m_metal)
        cyl(f"{name}_uflp{i}", 0.0008, 0.0024, (x, -d * 0.36, h / 2 + 0.0015), (0, 0, 0), m_dark)
    # 排针
    cube(f"{name}_hdr", (w * 0.22, d * 0.14, h * 0.35), (-w * 0.34, d * 0.36, h / 2), m_dark)


# ------------------------------------------------------------------ 场景
def setup(target, ortho, direction=(-0.18, -0.55, 0.82), res=(1200, 900)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = -0.05

    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 0.9

    bpy.ops.object.light_add(type='SUN', location=(1.5, -2, 3))
    sun = bpy.context.active_object
    sun.data.energy = 2.2
    sun.data.angle = math.radians(12)
    sun.rotation_euler = (math.radians(42), math.radians(6), math.radians(28))

    bpy.ops.object.light_add(type='AREA', location=(-1.2, -1.0, 1.2))
    ar = bpy.context.active_object
    ar.data.energy = 22
    ar.data.size = 2.0
    ar.rotation_euler = (math.radians(58), 0, math.radians(-40))

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    d = Vector(direction).normalized()
    tgt = Vector(target)
    cam.location = tgt + d * 2.0
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam


def render(name):
    bpy.context.scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print(f"[render] {name}", flush=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))


def main():
    specs = [
        ("MOD_R700", (0.214, 0.149, 0.030), 4, False, 0.30),
        ("MOD_R420", (0.190, 0.127, 0.033), 4, False, 0.27),
        ("MOD_FX9600", (0.273, 0.184, 0.051), 8, True, 0.38),
    ]
    for name, (w, d, h), ports, flange, ortho in specs:
        reset()
        build_reader(name, w, d, h, ports, flange)
        setup((0, 0, 0), ortho, direction=(-0.20, -0.52, 0.83))
        render(name)

    reset()
    build_module("MOD_M6E", 0.066, 0.036, 0.008)
    setup((0, 0, 0), 0.085, direction=(-0.25, -0.45, 0.86))
    render("MOD_M6E")
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
