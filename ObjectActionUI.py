'''
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
'''
bl_info = {
    "name": "Object Action UI",
    "author": "Dukhart",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "PROPERTIES > data",
    "description": "Displays the actions in an armatures nla tracklist",
    "doc_url": "https://github.com/Dukhart/ObjectActionUI",
    "category": "Properties",
}

import bpy

def isArmatureOrChildOf(obj):
    if obj.type == 'ARMATURE':
        return True
    else:
        while obj.parent:
            obj = obj.parent
            if obj.type == 'ARMATURE':
                return True
    return False
            

class OBJECTACTIONUI_OT_RenameBone(bpy.types.Operator):
    """Renames the bone on all connected actions"""
    bl_label = "Rename Bone"
    bl_idname = "objectactionui.renamebone"
    
    nla: bpy.props.BoolProperty(name="Use nla tracks", default=True, description='limits bone renaming to the nla track list')
    updateActive: bpy.props.BoolProperty(name="Update Active", default=True, description='will update active action even if it is not on the nla track list')
    oldName: bpy.props.StringProperty(name='Old Name')
    newName: bpy.props.StringProperty(name='New Name')
    
    def invoke(self, context, event):
        #if context.object.animation_data and context.object.animation_data.nla_tracks:
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
    def execute(self, context):
        print ('Execute Object Action UI')
        obj = context.object
        if not isArmatureOrChildOf(obj):
            self.report({'ERROR'},'No armature selected')
            return {'CANCELLED'}

        if obj.mode == 'EDIT':
            bone = obj.data.edit_bones.active
        else:
            bone = obj.data.bones.active
        
        #Check if user typed in different bone to change
        if not self.oldName == bone.name:
            if obj.mode == 'EDIT':
                i = obj.data.edit_bones.find(self.oldName)
                if i >= 0:
                    bone = obj.data.bones[i]
                else:
                    self.report({'ERROR'},'Input bone ' + self.oldName + ' not found')
                    return {'CANCELLED'}
            else:
                i = obj.data.bones.find(self.oldName)
                if i >= 0:
                    bone = obj.data.bones[i]
                else:
                    self.report({'ERROR'},'Input bone ' + self.oldName + ' not found')
                    return {'CANCELLED'}
        self.renameBone_ActionUpdate(obj, bone, self.newName)
        return {'FINISHED'}
    
    @staticmethod
    def renameActionDataPath(path, oldName, newName):
        pathParse  = path.split('"')
        
        preffix = pathParse[0]
        pathName = pathParse[1]
        suffix = pathParse[2]
        
        if pathName == oldName:
            newPath = preffix + '"' + newName + '"' + suffix
            return newPath
        else:
            return path
                          
    def renameBone_ActionUpdate(self, obj, bone, newName):
        if not obj.type == 'ARMATURE':
            self.report({'ERROR'},'No armature selected')
            return {'CANCELLED'}
        oldName = bone.name
        #store active action
        activeAction = None
        if obj.animation_data:
            activeAction = obj.animation_data.action
        
        if self.updateActive == False:
            #turn off acive action or it will update
            obj.animation_data.action = None
        
        data = obj.data
        #change bone name
        if obj.mode == 'EDIT':
            data.edit_bones.active.name = newName
        else:
            data.bones.active.name = newName
        #resore acitive action
        obj.animation_data.action = activeAction
        
        #update actions
        if self.nla:
            self.updateNLA(obj, oldName, bone.name)
        else:
            self.updateActions(obj, oldName, bone.name)
        
        
    #updates all actions with a matching bone name
    @classmethod
    def updateActions (cls, obj, oldName, newName):
        if not obj.type == 'ARMATURE':
            cls.report({'ERROR'},'No armature selected')
            return {'CANCELLED'}
    
        actions = bpy.data.actions
        if actions:
            for action in actions:
                print('Updating bones in: ' + action.name)
                if action:
                    for fcurve in action.fcurves:
                        if fcurve.group.name == oldName:
                            fcurve.group.name = newName
                        fcurve.data_path = cls.renameActionDataPath(fcurve.data_path, oldName, newName)
    
    #updates actions in the selected armatures nla track list with a matching bone
    @classmethod
    def updateNLA (cls, obj, oldName, newName):
        if not obj.type == 'ARMATURE':
            cls.report({'ERROR'},'No armature selected')
            return {'CANCELLED'}

        if not obj.animation_data:
            cls.report({'WARNING'}, obj.name + ' has no animation data')
            return {'CANCELLED'}
        for track in obj.animation_data.nla_tracks:
            for strip in track.strips:
                action = strip.action
                print('Updating bones in: ' + action.name)
                for fcurve in action.fcurves:
                    if fcurve.group.name == oldName:
                        fcurve.group.name = newName
                    fcurve.data_path = cls.renameActionDataPath(fcurve.data_path, oldName, newName)

#the panel displayed in the bone properties
class OBJECTACTIONUI_PT_Panel(bpy.types.Panel):
    """Renames the bone on all connected actions"""
    bl_label = "Actions"
    bl_idname = "OBJECTACTIONUI_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    
    def __init__(self):
        #clear the list
        self.clearList()
        #build the list
        self.buildList()
        
    #build
    @classmethod
    def buildList(cls):
        #builds the list based on current selections animation_data
        obj = bpy.context.object

        if obj and obj.animation_data and obj.animation_data.nla_tracks:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action:
                        n = bpy.context.scene.nla_actions_list.add()
                        n.name = strip.action.name
                        n.track = track.name
                        n.strip = strip.name
        
        #forces index to valid index
        if bpy.context.scene.nla_actions_index >= len(bpy.context.scene.nla_actions_list):
            bpy.context.scene.nla_actions_index = len(bpy.context.scene.nla_actions_list) - 1
        if bpy.context.scene.nla_actions_index < 0:
            bpy.context.scene.nla_actions_index = 0
        
    @classmethod
    def clearList(cls):
        #clear list starting at the end until 0
        list_index = len(bpy.context.scene.nla_actions_list)
        while list_index:
            list_index -= 1
            bpy.context.scene.nla_actions_list.remove(list_index)
            
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        obj = context.object
        row = layout.row()
        #row.label(text="Active armature is: " + obj.name)
        #get active bone
        if obj and obj.type == 'ARMATURE':
            if obj.mode == 'EDIT':
                bone = obj.data.edit_bones.active
            else:
                bone = obj.data.bones.active
            if bone:
                props = self.layout.operator('objectactionui.renamebone', text="Rename Bone")
                props.oldName = bone.name
                row = layout.row()
                row.label(text=obj.name, icon='ARMATURE_DATA')
                row.label(text=bone.name, icon='BONE_DATA')
                           
        # template_list
        layout.template_list("OBJECTACTIONUI_UL_List", "NLA_Action_List", scene, "nla_actions_list", scene, "nla_actions_index")
        layout.template_list("OBJECTACTIONUI_UL_List", "compact", scene, "nla_actions_list", scene, "nla_actions_index", type='COMPACT')
        
        #bottom button row
        row = layout.row()
        #select from existing actions
        #props = row.operator('nla_actions_list.add_action', text="Add Existing")
        props = row.menu('OBJECTACTIONUI_MT_Existing_Menu', text="Add Existing")
        #create a new action and assign it
        props = row.operator('objectactionui.new_nlaaction', text="New")
        
        #remove action from nla list
        props = row.operator('objectactionui.remove_nlaaction', text="Remove")

class OBJECTACTIONUI_ListItem(bpy.types.PropertyGroup):
    """Group of properties representing an item in the list.""" 
    name: bpy.props.StringProperty( name="Name", description="The Name", default="none")
    track: bpy.props.StringProperty( name="Track", description="The Track", default="none")
    strip: bpy.props.StringProperty( name="Strip", description="The Strip", default="none")

class OBJECTACTIONUI_UL_List(bpy.types.UIList):
    # The draw_item function is called for each item of the collection that is visible in the list.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        action = slot.name
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            '''
            if action:
                layout.prop(action, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
            '''
            layout.label(text=item.name, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            
#creates a new action and adds it to the objects nla tracks            
class OBJECTACTIONUI_OT_New_NLAAction(bpy.types.Operator):
    '''Add New Action'''
    bl_idname = "objectactionui.new_nlaaction"
    bl_label = "Create new Action"
    
    actionName: bpy.props.StringProperty(name='Action Name')
    
    def execute(self, context):
        obj = context.object
        if not obj:
            self.report({'ERROR'},'No object selected')
            return {'CANCELLED'}
        
        action = bpy.data.actions.new(self.actionName)
        
        if not obj.animation_data:
            obj.animation_data_create()
        track = obj.animation_data.nla_tracks.new()
        strip = track.strips.new(action.name + ' strip',0,action)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        
        return wm.invoke_props_dialog(self)
    
#find existing action and add it to the objects nla tracks
class OBJECTACTIONUI_OT_Add_NLAAction(bpy.types.Operator):
    """Renames the bone on all connected actions"""
    bl_idname = "objectactionui.add_nlaaction"
    bl_label = "Add Existing Action"
    
    actionName: bpy.props.StringProperty(name='Action Name')
    actionID: bpy.props.IntProperty(name='Action ID')
    
    @classmethod
    def poll(cls, context):
        return bpy.data.actions
    
    def execute(self, context):
        obj = context.object
        if not obj:
            self.report({'ERROR'},'No context.obj in ADD_NLAAction')
            return {'CANCELLED'}

        action = bpy.data.actions[self.actionID]
        if not obj.animation_data:
            obj.animation_data_create()
        track = obj.animation_data.nla_tracks.new()
        strip = track.strips.new(action.name + ' strip',0,action)
        return {'FINISHED'} 
    
#removes nla action from list optional delete action defaults to false            
class OBJECTACTIONUI_OT_Remove_NLAAction(bpy.types.Operator):
    '''Removes action from list. Hold CTRL to delete action'''
    bl_idname = "objectactionui.remove_nlaaction"
    bl_label = "Remove Action"
    
    deleteAction: bpy.props.BoolProperty(name='Delete Action', default=False)
    
    @classmethod
    def poll(cls, context):
        return context.scene.nla_actions_list
    
    def invoke(self, context, event):
        if event.ctrl:
            self.deleteAction = True
        else:
            self.deleteAction = False
        
        if context.object:
            obj  = context.object
            if not obj:
                self.report({'ERROR'},'No context.obj in Remove_NLAAction')
                return {'CANCELLED'}

            i = context.scene.nla_actions_index
            
            #validate index
            if i >= 0 and i < len(context.scene.nla_actions_list):
                s = context.scene.nla_actions_list[i].name
                #delete action if requested
                if self.deleteAction:
                    j = bpy.data.actions.find(s)
                    if j >= 0 and j < len(bpy.data.actions):
                        bpy.data.actions.remove(bpy.data.actions[j])
                #remove from this armature's nla_tracks
                elif obj.animation_data and obj.animation_data.nla_tracks:
                    s = context.scene.nla_actions_list[i].track
                    j = obj.animation_data.nla_tracks.find(s) 
                    if j >= 0:
                        obj.animation_data.nla_tracks.remove(obj.animation_data.nla_tracks[j])
                    
            else:
                warning('Invalid index')
                return {'CANCELLED'}
            
        self.cleanEmptyTracks(context)
        return {'FINISHED'}
    
    #removes empty nla tracks
    def cleanEmptyTracks(self, context):
        print('cleaning nla tracks')
        if context.object:
            obj  = context.object
            if not obj:
                self.report({'ERROR'},'No obj in CleanEmptyTracks')
                return {'CANCELLED'}

            if obj.animation_data:
                for track in obj.animation_data.nla_tracks:
                    if not track.strips:
                        print('removing ' + track.name + ' no strips')
                        obj.animation_data.nla_tracks.remove(track)
                    else:
                        hasAction = False
                        for strip in track.strips:
                            if not strip.action:
                                print('removing ' + track.name + " - " + strip.name + ' no action')
                                track.strips.remove(strip)
                            else:
                                hasAction = True
                        if not hasAction:
                            print('removing ' + track.name + ' no action')
                            obj.animation_data.nla_tracks.remove(track)
    
class OBJECTACTIONUI_MT_Existing_Menu(bpy.types.Menu):
    '''Add Existing Action'''
    bl_label = "Existing Actions"
    bl_idname = "OBJECTACTIONUI_MT_Existing_Menu"
    
    @classmethod
    def poll(cls, context):
        return bpy.data.actions
    
    def draw(self, context):
        layout = self.layout
        i = 0
        for action in bpy.data.actions:
            props = layout.operator('objectactionui.add_nlaaction', text=action.name)
            props.actionID = i
            i += 1
  
def register():
    #register classes
    bpy.utils.register_class(OBJECTACTIONUI_PT_Panel)
    bpy.utils.register_class(OBJECTACTIONUI_OT_RenameBone)
    bpy.utils.register_class(OBJECTACTIONUI_UL_List)
    bpy.utils.register_class(OBJECTACTIONUI_ListItem)
    bpy.utils.register_class(OBJECTACTIONUI_OT_New_NLAAction)
    bpy.utils.register_class(OBJECTACTIONUI_OT_Add_NLAAction)
    bpy.utils.register_class(OBJECTACTIONUI_OT_Remove_NLAAction)
    bpy.utils.register_class(OBJECTACTIONUI_MT_Existing_Menu)
    #register props
    bpy.types.Scene.nla_actions_list = bpy.props.CollectionProperty(type = OBJECTACTIONUI_ListItem) 
    bpy.types.Scene.nla_actions_index = bpy.props.IntProperty(name = "Index for nla_actions_list", default = 0)
    #bpy.types.Scene.bpy_action_index = bpy.props.IntProperty(name = "Index for bpy_actions_list", default = 0)
    #bpy.types.Scene.nla_last_object = bpy.props.StringProperty(name = "last object", default='')
    
def unregister():
    bpy.utils.unregister_class(OBJECTACTIONUI_PT_Panel)
    bpy.utils.unregister_class(OBJECTACTIONUI_OT_RenameBone)
    bpy.utils.unregister_class(OBJECTACTIONUI_UL_List)
    bpy.utils.unregister_class(OBJECTACTIONUI_ListItem)
    bpy.utils.unregister_class(OBJECTACTIONUI_OT_New_NLAAction)
    bpy.utils.unregister_class(OBJECTACTIONUI_OT_Add_NLAAction)
    bpy.utils.unregister_class(OBJECTACTIONUI_OT_Remove_NLAAction)
    bpy.utils.unregister_class(OBJECTACTIONUI_MT_Existing_Menu)
    del bpy.types.Scene.nla_actions_list
    del bpy.types.Scene.nla_actions_index
    #del bpy.types.Scene.bpy_action_index
    
if __name__ == "__main__":
    register()
