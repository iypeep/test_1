# -*- coding: utf-8 -*-
"""天线页下方：按厂家手册外形建的方形圆极化板状天线（Blender）。

三款（尺寸/增益均取手册）：
  5.5 dBi  Laird S9025PL   132 × 132 × 18 mm
  8   dBi  Silion SLP1002  225 × 225 × 35 mm（ABS 面罩 + 铸铝后壳，N-female）
  9   dBi  Laird S9028PCL  259 × 259 × 34 mm

外形要点：面罩 + 深色密封框 + 后壳（铝）+ 背面安装板 + N 型接头 + 尾缆/商标条，
正面 3/4 视角，透明底。

输出：_3d_out2/ANT_55.png / ANT_8.png / ANT_9.png
用法：blender -b -P rfid3d_antennas.py
"""
import bpy, math, os
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "_3d_out2")
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.5, metal=0.0):
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


def cyl(name, r, depth, loc, rot, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    return o


def build_antenna(name, w, h, t, front_rgb, back_rgb, trim_rgb):
    m_front = mat("front", front_rgb, 0.55)
    m_back = mat("back", back_rgb, 0.40, 0.35)
    m_trim = mat("trim", trim_rgb, 0.45)
    m_gasket = mat("gasket", (0.26, 0.27, 0.29), 0.7)
    m_metal = mat("metal", (0.56, 0.57, 0.59), 0.3, 0.9)
    m_dark = mat("dark", (0.07, 0.075, 0.085), 0.6)

    # 后壳（略小于面罩截面，形成后缘台阶）
    cube(f"{name}_body", (w * 0.985, t * 0.58, h * 0.985), (0, t * 0.18, 0), m_back, bevel=min(w, h) * 0.012)
    # 深色密封框
    cube(f"{name}_gasket", (w * 0.99, t * 0.10, h * 0.99), (0, -t * 0.28, 0), m_gasket, bevel=min(w, h) * 0.008)
    # 面罩
    cube(f"{name}_radome", (w * 0.90, t * 0.17, h * 0.90), (0, -t * 0.41, 0), m_front, bevel=min(w, h) * 0.016)
    # 面罩上的一圈细凹线（工艺槽）
    cube(f"{name}_groove", (w * 0.80, t * 0.012, h * 0.80), (0, -t * 0.495, 0), m_trim)
    # 底部小标签条
    cube(f"{name}_label", (w * 0.34, t * 0.012, h * 0.045), (0, -t * 0.515, -h * 0.30), m_trim)

    # 背面安装板 + N 接头 + 尾缆
    cube(f"{name}_plate", (w * 0.62, t * 0.07, h * 0.62), (0, t * 0.50, 0), m_metal, bevel=0.004)
    cyl(f"{name}_n", 0.0085, 0.018, (0, t * 0.56, -h * 0.16), (math.pi / 2, 0, 0), m_metal)
    cyl(f"{name}_pin", 0.0028, 0.020, (0, t * 0.57, -h * 0.16), (math.pi / 2, 0, 0), m_dark)


def setup(target, ortho, direction=(-0.52, -0.76, 0.38), res=(1200, 1000)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = 0.05

    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 1.0

    bpy.ops.object.light_add(type='SUN', location=(1.4, -2.2, 2.4))
    sun = bpy.context.active_object
    sun.data.energy = 2.4
    sun.data.angle = math.radians(10)
    sun.rotation_euler = (math.radians(48), math.radians(4), math.radians(28))

    bpy.ops.object.light_add(type='AREA', location=(-1.5, -1.2, 0.9))
    ar = bpy.context.active_object
    ar.data.energy = 22
    ar.data.size = 2.4
    ar.rotation_euler = (math.radians(62), 0, math.radians(-48))

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
    print("[render]", name, flush=True)


def main():
    specs = [
        ("ANT_55", 0.132, 0.132, 0.018, (0.79, 0.795, 0.80), (0.36, 0.37, 0.39), (0.62, 0.63, 0.64)),
        ("ANT_6", 0.128, 0.128, 0.020, (0.88, 0.88, 0.87), (0.52, 0.53, 0.55), (0.70, 0.71, 0.72)),
        ("ANT_8", 0.225, 0.225, 0.035, (0.88, 0.88, 0.87), (0.52, 0.53, 0.55), (0.70, 0.71, 0.72)),
        ("ANT_9", 0.259, 0.259, 0.034, (0.79, 0.795, 0.80), (0.36, 0.37, 0.39), (0.62, 0.63, 0.64)),
    ]
    for name, w, h, t, fr, bk, tr in specs:
        reset()
        build_antenna(name, w, h, t, fr, bk, tr)
        setup((0, 0, 0), w * 1.95)
        render(name)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
