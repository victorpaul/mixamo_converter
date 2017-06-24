# -*- coding: utf-8 -*-

'''
    Copyright (C) 2017  Enzio Probst
  
    Created by Enzio Probst

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from bpy_types import Object
import os

#function for removing all namespaces from strings, objects or even armatrure bones
def remove_namespace(s = ''):
    if type(s) == str:
        i = s[::-1].find(':')
        if i == -1:
            return s
        else:
            return s[-i::]
    elif type(s) == Object:
        if s.type == 'ARMATURE':
            for bone in s.data.bones:
                bone.name = remove_namespace(bone.name)
        s.name = remove_namespace(s.name)
        return 1
    return -1

#function to apply restoffset to rig, should be used if rest-/bindpose does not stand on ground with feet
def ApplyRestoffset(armature, hipbone, restoffset):
    # apply rest offset to restpose
    bpy.context.scene.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.transform.translate(value=restoffset, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    bpy.ops.object.mode_set(mode='OBJECT')

    # apply restoffset to animation of hip
    restoffset_local = (restoffset[0], restoffset[2], -restoffset[1])
    for axis in range(3):
        fcurve = armature.animation_data.action.fcurves.find("pose.bones[\""+hipbone.name+"\"].location", axis)
        for pi in range(len(fcurve.keyframe_points)):
            fcurve.keyframe_points[pi].co.y -= restoffset_local[axis]/armature.scale.x
    return 1

'''
function to bake hipmotion to RootMotion in MixamoRigs
'''
def HipToRoot(armature, use_x = True, use_y = True, use_z = True, on_ground = True, scale = 1.0, restoffset = (0,0,0), hipname='', fixbind = True, apply_transform = True):

    root = armature
    root.name = "root"
    framerange = root.animation_data.action.frame_range
    
    for hipname in ('Hips', 'mixamorig:Hips', hipname):
        hips = root.pose.bones.get(hipname)
        if hips != None:
            break
    if hips == None:
        return -1
    
    
    #Scale by ScaleFactor
    if scale != 1.0:
        for i in range(3):
            fcurve = root.animation_data.action.fcurves.find('scale', i)
            if fcurve != None:
                root.animation_data.action.fcurves.remove(fcurve)
        root.scale *= scale
    
    #apply restoffset to restpose and correct animation
    ApplyRestoffset(root, hips, restoffset)
    
    hiplocation_world = root.matrix_local * hips.bone.head
    z_offset = hiplocation_world[2]
    
    #Create helper to bake the root motion
    bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, view_align=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    rootBaker = bpy.context.object
    rootBaker.name = "rootBaker"

    if use_z:
        print("using z")
        bpy.ops.object.constraint_add(type='COPY_LOCATION')
        bpy.context.object.constraints["Copy Location"].name = "Copy Z_Loc"
        bpy.context.object.constraints["Copy Z_Loc"].target = root
        bpy.context.object.constraints["Copy Z_Loc"].subtarget = hips.name
        bpy.context.object.constraints["Copy Z_Loc"].use_x = False
        bpy.context.object.constraints["Copy Z_Loc"].use_y = False
        bpy.context.object.constraints["Copy Z_Loc"].use_z = True
        bpy.context.object.constraints["Copy Z_Loc"].use_offset = True
        if on_ground:
            print("using on ground")
            rootBaker.location[2] = -z_offset
            bpy.ops.object.constraint_add(type='LIMIT_LOCATION')
            bpy.context.object.constraints["Limit Location"].use_min_z = True        

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].use_x = use_x
    bpy.context.object.constraints["Copy Location"].use_y = use_y
    bpy.context.object.constraints["Copy Location"].use_z = False
    bpy.context.object.constraints["Copy Location"].target = root
    bpy.context.object.constraints["Copy Location"].subtarget = hips.name

    bpy.ops.object.constraint_add(type='COPY_ROTATION')
    bpy.context.object.constraints["Copy Rotation"].target = root
    bpy.context.object.constraints["Copy Rotation"].subtarget = hips.name
    bpy.context.object.constraints["Copy Rotation"].use_y = False
    bpy.context.object.constraints["Copy Rotation"].use_x = False

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=False, bake_types={'OBJECT'})

    #Create helper to bake hipmotion in Worldspace
    bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, view_align=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    hipsBaker = bpy.context.object
    hipsBaker.name = "hipsBaker"

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].target = root
    bpy.context.object.constraints["Copy Location"].subtarget = hips.name

    bpy.ops.object.constraint_add(type='COPY_ROTATION')
    bpy.context.object.constraints["Copy Rotation"].target = root
    bpy.context.object.constraints["Copy Rotation"].subtarget = hips.name

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=False, bake_types={'OBJECT'})

    #select armature
    root.select = True
    bpy.context.scene.objects.active = root
    
    if apply_transform:
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    #Bake Root motion to Armature (root)
    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].target = rootBaker

    bpy.ops.object.constraint_add(type='COPY_ROTATION')
    bpy.context.object.constraints["Copy Rotation"].target = bpy.data.objects["rootBaker"]
    bpy.context.object.constraints["Copy Rotation"].use_offset = True

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'OBJECT'})


    bpy.ops.object.mode_set(mode = 'POSE')
    hips.bone.select = True
    root.data.bones.active = hips.bone

    bpy.ops.pose.constraint_add(type='COPY_LOCATION')
    hips.constraints["Copy Location"].target = hipsBaker
    bpy.ops.pose.constraint_add(type='COPY_ROTATION')
    hips.constraints["Copy Rotation"].target = hipsBaker

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'POSE'})
    
    
    
    #Delete helpers
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    hipsBaker.select = True
    rootBaker.select = True

    bpy.ops.object.delete(use_global=False)
    
    # bind armature to dummy mesh if it doesn't have any
    if fixbind:
        bindmesh = None
        for child in root.children:
            for mod in child.modifiers:
                if mod.type == 'ARMATURE':
                    if mod.object == root:
                        bindmesh = child
                        break
        if bindmesh == None:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.mesh.primitive_plane_add(radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
            binddummy = bpy.context.object
            binddummy.name = 'binddummy'
            root.select = True
            bpy.context.scene.objects.active = root
            bpy.ops.object.parent_set(type='ARMATURE')
        elif apply_transform:
            bindmesh.select = True
            bpy.context.scene.objects.active = bindmesh
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    return 1
    
#End of HipToRoot Function

'''
Batch Convert MixamoRigs
'''
def BatchHipToRoot(source_dir, dest_dir, use_x = True, use_y = True, use_z = True, on_ground = True, scale = 1.0, restoffset = (0,0,0), hipname = '', fixbind = True, apply_transform = True, remove_namespace = True):
    numfiles = 0
    for file in os.scandir(source_dir):
        if file.name[-4::] == ".fbx":
            numfiles += 1
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=True)
            #remove all datablocks
            for mesh in bpy.data.meshes:
                bpy.data.meshes.remove(mesh, do_unlink=True)
            for material in bpy.data.materials:
                bpy.data.materials.remove(material, do_unlink=True)
            for action in bpy.data.actions:
                    bpy.data.actions.remove(action, do_unlink=True)
            #import FBX
            bpy.ops.import_scene.fbx(filepath=file.path, axis_forward='-Z', axis_up='Y', directory="", filter_glob="*.fbx", ui_tab='MAIN', use_manual_orientation=False, global_scale=1, bake_space_transform=False, use_custom_normals=True, use_image_search=True, use_alpha_decals=False, decal_offset=0, use_anim=True, anim_offset=1, use_custom_props=True, use_custom_props_enum_as_string=True, ignore_leaf_bones=True, force_connect_children=False, automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X', use_prepost_rot=True)
            #namespace removal
            if remove_namespace:
                for obj in bpy.context.selcted_objects:
                    remove_namespace(obj)
            
            def getArmature(objects):
                for a in objects:
                    if a.type == 'ARMATURE':
                        return a
            armature = getArmature(bpy.context.selected_objects)
            #do hip to Root conversion
            if HipToRoot(armature, use_x = use_x, use_y = use_y, use_z = use_z, on_ground = on_ground, scale = scale, restoffset = restoffset, hipname = hipname, fixbind = fixbind, apply_transform = apply_transform) == -1:
                return -1
            
            #remove newly created orphan actions
            for action in bpy.data.actions:
                if action != armature.animation_data.action:
                    bpy.data.actions.remove(action, do_unlink=True)

            bpy.ops.export_scene.fbx(filepath=dest_dir + file.name, use_selection=False)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            print("%d files converted" % numfiles)
    return numfiles

if __name__ == "__main__":
    print("mixamoconv Hello.")
