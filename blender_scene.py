import argparse, math, os, sys
import bpy
from mathutils import Vector
def mat(name,c):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); return m
def ball(name,p,s,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=p); o=bpy.context.object; o.name=name; o.scale=s; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o
def look(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat("-Z","Y").to_euler()
def scene(i,path):
 bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
 palettes=[((.48,.78,.98),(.22,.62,.32),(.1,.38,.18)),((.08,.32,.58),(.12,.62,.78),(.96,.72,.24)),((.1,.12,.3),(.28,.24,.55),(.65,.42,.82)),((.88,.72,.48),(.6,.42,.24),(.22,.55,.3))]
 sky,ground,accent=palettes[i%4]; M={n:mat(n,c) for n,c in {"ground":ground,"accent":accent,"skin":(1,.57,.2),"cream":(1,.85,.62),"white":(1,1,1),"black":(.02,.03,.05),"green":(.12,.42,.18)}.items()}
 world=bpy.data.worlds.new("Cartoon World"); bpy.context.scene.world=world; world.color=sky
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.1)); bpy.context.object.data.materials.append(M["ground"])
 for x in [-5,5]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.22,depth=2.4,location=(x,1,1.2)); bpy.context.object.data.materials.append(M["cream"])
  ball("Tree crown",(x,1,2.7),(1.1,.7,1.1),M["green"])
 # Mascot parts parented to one root so the whole character moves together.
 root=bpy.data.objects.new("Mascot root",None); bpy.context.collection.objects.link(root)
 for name,p,s,m in [("Body",(0,0,1.45),(.72,.52,.95),"skin"),("Belly",(0,-.46,1.35),(.48,.1,.58),"cream"),("Head",(0,-.02,2.65),(.88,.68,.78),"skin"),("Left ear",(-.65,0,3.22),(.23,.22,.34),"skin"),("Right ear",(.65,0,3.22),(.23,.22,.34),"skin"),("Left eye",(-.31,-.64,2.75),(.16,.09,.21),"white"),("Right eye",(.31,-.64,2.75),(.16,.09,.21),"white"),("Left pupil",(-.31,-.72,2.74),(.065,.045,.12),"black"),("Right pupil",(.31,-.72,2.74),(.065,.045,.12),"black"),("Smile",(0,-.69,2.3),(.2,.05,.07),"black"),("Left foot",(-.38,0,.52),(.27,.34,.22),"accent"),("Right foot",(.38,0,.52),(.27,.34,.22),"accent")]:
  o=ball(name,p,s,M[m]); o.parent=root
 arms=[]
 for x,side in [(-.78,-1),(.78,1)]:
  o=ball("Waving arm",(x,0,1.75),(.2,.2,.52),M["skin"]); o.parent=root; arms.append((o,side))
 # Different props and palette per story scene
 if i%4==0:
  for x in [-2.8,2.8]: ball("Flower",(x,-.1,.38),(.22,.22,.22),M["cream"])
 elif i%4==1:
  for x in [-3,3]: ball("Ocean bubble",(x,-.2,1.8),(.28,.28,.28),M["white"])
 elif i%4==2:
  for x,z in [(-3,3.5),(3,4),(2.6,2)]: ball("Planet",(x,.7,z),(.4,.4,.4),M["accent"])
 else:
  for x in [-2.8,2.8]:
   bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.55,depth=1,location=(x,0,.55)); bpy.context.object.data.materials.append(M["accent"])
 for frame,z in [(1,0),(13,.16),(25,0),(37,.16),(49,0)]:
  root.location.z=z; root.keyframe_insert(data_path="location",frame=frame)
 for arm,side in arms:
  for frame,angle in [(1,-.3),(13,-.9),(25,-.3),(37,.1),(49,-.3)]:
   arm.rotation_euler[1]=side*angle; arm.keyframe_insert(data_path="rotation_euler",frame=frame)
 for ob in bpy.data.objects:
  if ob.animation_data and ob.animation_data.action:
   for fc in ob.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation="SINE"
    fc.modifiers.new("CYCLES")
 bpy.ops.object.camera_add(location=(0,-13,5)); cam=bpy.context.object; look(cam,(0,0,2)); cam.data.type="ORTHO"; cam.data.ortho_scale=12.5; bpy.context.scene.camera=cam
 bpy.ops.object.light_add(type="AREA",location=(-4,-5,8)); lamp=bpy.context.object; lamp.data.energy=1500; lamp.data.shape="DISK"; lamp.data.size=7; look(lamp,(0,0,1.5))
 s=bpy.context.scene; s.render.engine="BLENDER_EEVEE_NEXT"; s.render.resolution_x=960; s.render.resolution_y=540; s.render.resolution_percentage=100; s.render.fps=12; s.frame_start=1; s.frame_end=48
 s.render.image_settings.file_format="FFMPEG"; s.render.ffmpeg.format="MPEG4"; s.render.ffmpeg.codec="H264"; s.render.filepath=os.path.abspath(path); s.view_settings.view_transform="Standard"
 bpy.ops.render.render(animation=True)
def main():
 av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []; p=argparse.ArgumentParser(); p.add_argument("--output",default="output/scenes"); p.add_argument("--count",type=int,default=8); a=p.parse_args(av); os.makedirs(a.output,exist_ok=True)
 for i in range(a.count): print("Rendering scene",i+1,flush=True); scene(i,os.path.join(os.path.abspath(a.output),"scene_{:02d}".format(i+1)))
if __name__=="__main__": main()
