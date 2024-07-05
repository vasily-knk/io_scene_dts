import bpy
import os

scene = bpy.context.scene
list_of_empties = []

#Getting the lenght on the animation sequence
last_marker = max(scene.timeline_markers, key=lambda marker: marker.frame)
scene.frame_end = last_marker.frame

#Selecting the target armature
def find_armature():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
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

#Getting Transform data for one of the empties
def get_empty_transforms(empty):
     empty_transforms = {}
     for current_frame in range(last_marker.frame + 1):
         bpy.context.scene.frame_set(current_frame)
         print("Getting transform data for {0}, frame #{1}".format(empty.name, current_frame))
         empty_transforms[current_frame] = {
              'location' : empty.location,
              'rotation' : empty.rotation_quaternion,
              'scale' : empty.scale
         }
     return empty_transforms
         
#Getting all of the Empty's Children names
def fetch_empty_names(empty):
    for child in empty.children:
        list_of_empties.append(child.name)
        print(child.name)
        fetch_empty_names(child)

def fetch_empty_keyframes(empty):
    empty_transforms = {}
    index = 0
    list_of_empties.append(empty.name)  #Adding the first (parent) empty
    fetch_empty_names(empty)            #Adding all of the child empties
    print(list_of_empties)              #Debug

    for current_empty_name in list_of_empties:
         for obj in bpy.context.scene.objects:
              if obj.name == current_empty_name:
                bpy.context.scene.objects.active = obj
                obj.select = True
                empty_transforms[index] = {current_empty_name : get_empty_transforms(obj)}
                index += 1
    return empty_transforms
         

def struc_for_arm(armature):
    print(armature)

def transfer_keyframes():
    empty = find_empty()
    get_empty_transforms(empty)
    ref_transforms = fetch_empty_keyframes(empty)
    find_armature()


    bpy.ops.object.select_all(action='DESELECT')
    print("========Done========")
    


transfer_keyframes()