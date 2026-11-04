"""
Low-cost procedural 3D cartoon scene renderer.
Run with: blender -b --python blender_scene.py -- --output output/scenes --count 8
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

FPS = 12
LOOP_SECONDS = 4
WIDTH, HEIGHT = 960, 540


def args():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/scenes")
    parser.add_argument("--count", type=int, default=8)
    return parser.parse_args(values)


def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def uv(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bevel = obj.modifiers.new("Soft cartoon edges", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return assign(obj, mat)


def cone(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=radius, radius2=0,
                                    depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return assign(obj, mat)


def key_loop(obj, data_path, index, values):
    for frame, value in values:
        obj.keyframe_insert(data_path=data_path, index=index, frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "SINE"
            curve.modifiers.new("CYCLES")


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_scene(theme_index, output_path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    palettes = [
        ((0.48, 0.78, 0.98), (0.30, 0.72, 0.36), (0.12, 0.42, 0.18)),
        ((0.62, 0.84, 0.98), (0.20, 0.56, 0.30), (0.08, 0.32, 0.16)),
        ((0.05, 0.30, 0.55), (0.12, 0.62, 0.78), (0.95, 0.72, 0.24)),
        ((0.08, 0.10, 0.28), (0.20, 0.18, 0.48), (0.48, 0.35, 0.82)),
        ((0.72, 0.84, 0.98), (0.64, 0.72, 0.82), (0.30, 0.48, 0.72)),
        ((0.58, 0.78, 0.98), (0.65, 0.58, 0.36), (0.40, 0.26, 0.12)),
        ((0.95, 0.70, 0.72), (0.24, 0.62, 0.38), (0.96, 0.48, 0.20)),
        ((0.48, 0.68, 0.88), (0.34, 0.52, 0.32), (0.72, 0.42, 0.68)),
    ]
    sky, ground, accent = palettes[theme_index % len(palettes)]
    mats = {
        "sky": material("Sky", sky),
        "ground": material("Ground", ground),
        "accent": material("Accent", accent),
        "skin": material("Warm golden character", (1.0, 0.62, 0.24)),
        "belly": material("Cream belly", (1.0, 0.86, 0.62)),
        "white": material("Eye white", (1.0, 1.0, 1.0)),
        "black": material("Pupils", (0.025, 0.035, 0.06)),
        "mouth": material("Smile", (0.22, 0.055, 0.045)),
        "leaf": material("Leaves", (0.12, 0.48, 0.22)),
    }

    world = bpy.data.worlds.new("Cartoon world") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*sky, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.12))
    assign(bpy.context.object, mats["ground"])

    # Distant rounded hills
    for x, z, sx, sz in [(-5, 0.0, 3.0, 1.5), (4.8, 0.0, 3.5, 1.8), (0, -0.3, 5, 1.0)]:
        uv("Soft background hill", (x, 2.0, z), (sx, 0.45, sz), mats["accent"])

    # Trees or stylized scene props, varied per scene.
    for x in (-5.0, 5.0):
        cylinder("Tree trunk", (x, 1.1, 1.25), 0.22, 2.5, mats["belly"])
        uv("Tree crown", (x, 1.0, 2.65), (1.15, 0.65, 1.15), mats["leaf"])
        uv("Tree crown highlight", (x - 0.35, 0.35, 2.9), (0.48, 0.32, 0.5), mats["ground"])

    # Soft clouds / decorative floating shapes
    for x, z in [(-3.8, 5.1), (3.7, 4.8)]:
        uv("Cloud", (x, 2.2, z), (1.0, 0.35, 0.38), mats["white"])
        uv("Cloud puff", (x + 0.65, 2.2, z + 0.1), (0.65, 0.3, 0.32), mats["white"])

    # Main friendly 3D mascot, deliberately reused across every scene.
    root = bpy.data.objects.new("Mascot root", None)
    bpy.context.collection.objects.link(root)
    body = uv("Mascot body", (0, 0, 1.55), (0.82, 0.55, 1.05), mats["skin"])
    body.parent = root
    belly = uv("Mascot belly", (0, -0.48, 1.45), (0.53, 0.12, 0.65), mats["belly"])
    belly.parent = root
    head = uv("Mascot head", (0, -0.02, 2.75), (0.95, 0.72, 0.82), mats["skin"])
    head.parent = root

    for x in (-0.72, 0.72):
        ear = uv("Round ear", (x, 0.0, 3.30), (0.25, 0.24, 0.38), mats["skin"])
        ear.parent = root
    for x in (-0.34, 0.34):
        eye = uv("Eye", (x, -0.68, 2.85), (0.18, 0.12, 0.25), mats["white"])
        eye.parent = root
        pupil = uv("Pupil", (x, -0.79, 2.84), (0.075, 0.055, 0.13), mats["black"])
        pupil.parent = root
    smile = uv("Smile", (0, -0.73, 2.43), (0.23, 0.055, 0.09), mats["mouth"])
    smile.parent = root

    arms = []
    for x, side in [(-0.82, -1), (0.82, 1)]:
        arm = uv("Animated arm", (x, -0.02, 1.88), (0.22, 0.22, 0.58), mats["skin"])
        arm.parent = root
        arm.rotation_euler[1] = side * -0.35
        arms.append((arm, side))

    for x in (-0.38, 0.38):
        leg = uv("Foot", (x, 0.0, 0.58), (0.28, 0.38, 0.24), mats["accent"])
        leg.parent = root

    # Scene-specific props in the foreground.
    prop_mat = mats["accent"]
    if theme_index % 8 in (0, 1, 6, 7):
        for x in (-3.0, 3.0):
            uv("Flower center", (x, -0.2, 0.45), (0.18, 0.18, 0.18), mats["belly"])
            for a in range(5):
                angle = a * math.tau / 5
                uv("Flower petal", (x + math.cos(angle)*0.25, -0.2, 0.45 + math.sin(angle)*0.25),
                   (0.15, 0.12, 0.15), mats["white"])
    elif theme_index % 8 == 2:
        for x in (-3.2, 3.2):
            uv("Ocean bubble", (x, -0.3, 1.4 + (x > 0)*1.0), (0.28, 0.28, 0.28), mats["white"])
    elif theme_index % 8 == 3:
        for x, z in [(-3.4, 3.5), (3.3, 4.0), (2.8, 2.0)]:
            uv("Planet", (x, 0.8, z), (0.42, 0.42, 0.42), mats["accent"])
    else:
        for x in (-3.0, 3.0):
            cylinder("Learning prop", (x, 0.1, 0.65), 0.45, 0.9, prop_mat)

    # Mascot bob and arm wave; cycles modifier makes the action loop.
    root.location.z = 0
    key_loop(root, "location", 2, [(1, 0.0), (13, 0.16), (25, 0.0), (37, 0.16), (49, 0.0)])
    for arm, side in arms:
        key_loop(arm, "rotation_euler", 1, [
            (1, side * -0.35), (13, side * -0.95), (25, side * -0.35),
            (37, side * 0.15), (49, side * -0.35)
        ])

    # Camera and soft lighting.
    bpy.ops.object.camera_add(location=(0, -13.5, 5.1))
    camera = bpy.context.object
    look_at(camera, (0, 0, 2.2))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 12.8
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(-4, -6, 9))
    key = bpy.context.object
    key.data.energy = 1250
    key.data.shape = "DISK"
    key.data.size = 7
    look_at(key, (0, 0, 1.5))

    bpy.ops.object.light_add(type="AREA", location=(5, 1, 6))
    fill = bpy.context.object
    fill.data.energy = 700
    fill.data.size = 5
    look_at(fill, (0, 0, 2))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = FPS * LOOP_SECONDS
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = output_path
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.camera.data.lens = 50
    scene.render.image_settings.color_mode = "RGB"
    scene.frame_set(1)
    return scene


def main():
    options = args()
    os.makedirs(options.output, exist_ok=True)
    for index in range(options.count):
        target = os.path.abspath(os.path.join(options.output, "scene_{:02d}".format(index + 1)))
        print("Rendering 3D cartoon scene {}/{}".format(index + 1, options.count), flush=True)
        setup_scene(index, target)
        bpy.context.scene.render.filepath = target
        bpy.ops.render.render(animation=True)
    print("3D SCENES RENDERED", flush=True)


if __name__ == "__main__":
    main()
