import bpy
import os
import numpy
import math
import mathutils

scene = bpy.context.scene
quaternion = mathutils.Quaternion
list_of_empties = []
list_of_bones = []

#Getting the lenght on the animation sequence
scene.frame_start = 0
start_sequence_frame = 0
last_marker = max(scene.timeline_markers, key=lambda marker: marker.frame)
scene.frame_end = last_marker.frame
#keyframe_range = len(range(start_sequence_frame, last_marker.frame + 1))
keyframe_range = range(start_sequence_frame, 20)

rotation_bias_rad = (90 * numpy.pi) / 180

def quaternion_to_euler(quaternion):
    w, x, y, z = quaternion

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    # Convert from radians to degrees
    roll = math.degrees(roll)
    pitch = math.degrees(pitch)
    yaw = math.degrees(yaw)

    return (roll, pitch, yaw)

#Selecting the target armature
def find_armature():
    print("Looking for the Armature")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            bpy.context.scene.objects.active = obj
            obj.select = True
            return obj
    #TODO Handle exceptions

#Selecting the reference Empty
def find_empty():
    print("Looking for Root Empty")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and obj.name == "Bip01":
            bpy.context.scene.objects.active = obj
            obj.select = True
            return obj
    #TODO Handle exceptions


"""
#Getting Transform data for one of the empties
def get_empty_transforms(empty):
     single_empty_transforms = {}
     for current_frame in keyframe_range:
         bpy.context.scene.frame_set(current_frame)
         print("Getting transform data for {0}, frame #{1}".format(empty.name, current_frame))
         single_empty_transforms[current_frame] = {
              'location' : empty.location,
              'rotation' : empty.rotation_quaternion,
              'scale' : empty.scale
         }
     if empty.name == "Bip01":
        print("Transforms:", single_empty_transforms)
     return single_empty_transforms
  """       
#Storing Empties' biases
def get_transform_bias(transforms):
    transform_bias_dict = {}
    for current_empty in transforms:
        transform_bias = transforms[current_empty][0]
        transform_bias_dict.update({current_empty : transform_bias})
    return transform_bias_dict

#Getting all of the Empty's Children names
def fetch_empty_names(empty):
    for child in empty.children:
        list_of_empties.append(child.name)
        #print(child.name)
        fetch_empty_names(child)

#Collecting all of the transform data per Empty per Frame
def fetch_empty_keyframes(empty):
    list_of_empties.append(empty.name)  #Adding the first (parent) empty
    fetch_empty_names(empty)            #Adding all of the child empties
    print("List of Empties: \n", list_of_empties)              #Debug
    transform_registry = {}
    for current_empty_name in list_of_empties:
        for obj in bpy.context.scene.objects:
              if obj.name == current_empty_name:
                bpy.context.scene.objects.active = obj
                obj.select = True
                print("Currently busy with {} Empty".format(bpy.context.scene.objects.active.name))
                frame_registry = {}
                for current_frame in keyframe_range:
                    bpy.context.scene.frame_set(current_frame)
                    #print("Getting transform data for {0}, frame #{1}, location data is {2}, rotation data is {3}".format(obj, current_frame, obj.location, obj.rotation_quaternion))
                    frozen_location = tuple(obj.location)
                    frozen_rotation = tuple(obj.rotation_quaternion)
                    #frozen_rotation = tuple(quaternion_to_euler(obj.rotation_quaternion))
                    frozen_scale = tuple(obj.scale)
                    frame_registry[current_frame] = {'location' : frozen_location,
                                                     'rotation' : frozen_rotation,
                                                     'scale' : frozen_scale
                                                     }
                transform_registry.update({current_empty_name : frame_registry})
                #print(transform_registry)
 
    return transform_registry
         
#Setting all of the Transform data per Bone per frame
def set_armature_keyframes(armature, ref_transforms, transform_bias):
    bpy.ops.object.posemode_toggle()
    for bone in armature.pose.bones:
        for ref_name in ref_transforms:
            if bone.name == ref_name:
                #print("I have matched {0} with {1}, setting up the keyframes".format(bone.name, ref_name))
                for current_frame in keyframe_range:
                    bpy.context.scene.frame_set(current_frame)
                    location_delta = tuple(numpy.subtract(ref_transforms[ref_name][current_frame]['location'], transform_bias[ref_name]['location']))

                    #Empty Quan rotaion -> Euler, bias shortcut, rotation bias fix
                    ref_rotation_euler = numpy.degrees(mathutils.Quaternion(ref_transforms[ref_name][current_frame]['rotation']).to_euler('XYZ'))
                    rotation_bias = numpy.degrees(mathutils.Quaternion(transform_bias[ref_name]['rotation']).to_euler('XYZ'))
                    rotation_delta = (ref_rotation_euler[0] - rotation_bias[0], ref_rotation_euler[1] - rotation_bias[1], ref_rotation_euler[2] - rotation_bias[2])
                    
                    #scale_delta = tuple(numpy.subtract(ref_transforms[ref_name][current_frame]['scale'], transform_bias[ref_name]['scale']))

                    if bone.name == "Bip01":
                        print("Empty location is {0}, Bip's starting location is {1}, and the bias is {2}, so the final location would be {3}".format(ref_transforms[ref_name][current_frame]['location'], bone.location, transform_bias[ref_name]['location'], location_delta))
                        print("Empty rotation is {0} which should be {1} in Euler".format(ref_transforms[ref_name][current_frame]['rotation'], ref_rotation_euler))
                        print("Empty Euler rotation is {0}, Bip's starting rotation is {1}, and the bias is {2}, so the final rotation would be {3}".format(ref_rotation_euler, bone.rotation_euler, rotation_bias, rotation_delta))
                        print("\n")
                    bone.location = location_delta
                    bone.keyframe_insert(data_path="location", frame=current_frame)

                    bone.rotation_mode = 'XYZ'
                    bone.rotation_euler = rotation_delta
                    bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
                    if bone.name == "Bip01":
                        print("Just inserted {} as Rotation".format(bone.rotation_euler))

                    bone.scale = ref_transforms[ref_name][current_frame]['scale']
                    bone.keyframe_insert(data_path="scale", frame=current_frame)
    bpy.ops.object.posemode_toggle()



    




def transfer_keyframes():
    empty = find_empty()                                                #Finding the root Empty
    ref_transforms = fetch_empty_keyframes(empty)                       #Collecting all of the transform data per Empty per Frame
    transform_bias = get_transform_bias(ref_transforms)                 #Collecting the 0-frame bias
    armature = find_armature()                                          #Finfing the Armature
    set_armature_keyframes(armature, ref_transforms, transform_bias)    #Setting the Armature keyframes
    for j in ref_transforms:
        if j == "Bip01":
            print("\n")
            print(ref_transforms[j])
            print("\n")
            print(transform_bias[j])
    bpy.ops.object.select_all(action='DESELECT')
    #print(ref_transforms)
    scene.frame_current = 0
    print("========Done========")
    


transfer_keyframes()