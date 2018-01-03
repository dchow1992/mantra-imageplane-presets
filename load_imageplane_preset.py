import json, os
def genKeyframes(key_list):
    #key_list = parm_dict['value']
    keys_to_add = []
    for k in key_list:                                        
        if k['type'] == 'StringKeyframe':
            key = hou.StringKeyframe()
            key.setExpression(k['expr'], hou.exprLanguage.Hscript if k['lang'] == 'Hscript' else hou.exprLanguage.Python)
            key.setTime(k['t'])
            keys_to_add.append(key)
        elif k['type'] == 'ChanRefKeyframe':
            key = hou.Keyframe()
            key.setExpression(k['expr'], hou.exprLanguage.Hscript if k['lang'] == 'Hscript' else hou.exprLanguage.Python)
            key.setAccel(k['a'])
            key.interpretAccelAsRatio(k['use_accel_ratio'])
            key.setSlope(k['s'])
            key.setTime(k['t'])
            key.setValue(k['v'])
            keys_to_add.append(key)
        elif k['type'] == 'BezierKeyframe':                                                
            key = hou.Keyframe()
            key.setExpression(k['expr'], hou.exprLanguage.Hscript if k['lang'] == 'Hscript' else hou.exprLanguage.Python)                                                        
            key.interpretAccelAsRatio(k['use_accel_ratio'])
            key.setSlope(k['s'])
            key.setTime(k['t'])
            key.setValue(k['v'])
            key.setAccel(k['out_a'])
            key.setSlopeAuto(k['auto_slopes'])
            if len(key_list) > 1:
                key.setInAccel(k['in_a'])                                                            
            keys_to_add.append(key)
    return keys_to_add 

def aovPresetLoad():
    s = hou.selectedNodes()

    if len(s) > 0:
        #select preset file    
        default_dir = '/home/dchow/scripts/json_temp/'
        infile = hou.ui.selectFile(start_directory=default_dir, title='Load Preset', pattern='*.json', chooser_mode=hou.fileChooserMode.Read)
        data = {}

        #open preset
        if os.path.isfile(infile):
            with open(infile) as jsonfile:
                data = json.load(jsonfile)

            #if file contains ms_aovPreset key
            if data.has_key('ms_aovPreset'):
                default = True 

                for rop in s:
                    if rop.type().name() == 'ifd':   
                        #extra image planes tab parmTemplates, quickplane parmTemplate, img plane parms
                        p = [a for a in rop.parmTemplateGroup().findFolder('Images').parmTemplates() if a.label() == 'Extra Image Planes'][0].parmTemplates()
                        qpp = [a for a in p if 'quickplane' in a.name()]
                        ipp = rop.parm('vm_numaux').parmTemplate().parmTemplates()

                        #default parms test                                        
                        for x in qpp:
                            if rop.evalParm(x.name()) != x.defaultValue():
                                default = False
                        if rop.evalParm('vm_numaux') != 0:
                            default = False                    
                        if not rop.parm('vm_exportcomponents').isAtDefault():
                            default = False

                if not default:
                    #behaviors
                    label = 'Some ROPS have existing image planes - what would you like to do?'
                    buttons = ('Merge Preset, (Priority: Preset)', 'Merge Preset, (Priority: ROP)', 'Replace', 'Cancel')
                    behavior = hou.ui.displayMessage(label, buttons=buttons)
                    behavior2 = 0

                    if behavior != 3:
                        #export comp and quickplane popup
                        if behavior == 0 or behavior == 1:                    
                            label2 = 'Mode: ' + buttons[behavior] + '\n\n\n How would you like to treat \n Export Components / Quickplanes?'
                            buttons2 = ('Use Preset', 'Use ROP')
                            behavior2 = hou.ui.displayMessage(label2, buttons=buttons2)

                        for rop in s:                    
                            if rop.type().name() == 'ifd':
                                #extra image planes tab parmTemplates, quickplane parmTemplate, img plane parms
                                p = [a for a in rop.parmTemplateGroup().findFolder('Images').parmTemplates() if a.label() == 'Extra Image Planes'][0].parmTemplates()
                                qpp = list(rop.parmsInFolder(('Images', 'Extra Image Planes')))
                                ipp = rop.parm('vm_numaux').parmTemplate().parmTemplates()

                                #merge behavior
                                if behavior < 2:                            
                                    if behavior2 == 0:                                
                                        #Use Preset Mode - quickplanes and export components 
                                        exp_comp = json.loads(json.dumps(data['vm_exportcomponents']))                               

                                        if not exp_comp.has_key('keyframes'):
                                            rop.parm('vm_exportcomponents').set(exp_comp['value'])
                                        else:                                    
                                            #keyframe / expression mode
                                            key_list = exp_comp['value']
                                            keys_to_add = genKeyframes(key_list)
                                            rop.parm('vm_exportcomponents').setKeyframes(tuple(keys_to_add))

                                        for x in qpp:
                                            parm_dict = json.loads(json.dumps(data[x.name()]))                                    
                                            if not parm_dict.has_key('keyframes'):
                                                x.set(parm_dict['value'])
                                            else:
                                                #quickplane keyframes / expressions
                                                key_list = parm_dict['value']
                                                keys_to_add = genKeyframes(key_list)
                                                x.setKeyframes(tuple(keys_to_add))

                                    #image plane merge - ropdict = dictionary with rop aov names as keys, pdict is same but preset aov names as keys
                                    ropdict = {}
                                    for i in range(1, rop.evalParm('vm_numaux')+1):
                                        ropparm = rop.parm('vm_variable_plane' + '{x}'.format(x=i))                                                               
                                        ropdict[ropparm.eval()] = i

                                    pdict = {}
                                    expand_numaux = json.loads(json.dumps(data['vm_numaux']))
                                    for i in range(1, expand_numaux['value']+1):

                                        preset_dict = json.loads(json.dumps(data['vm_variable_plane' + '{x}'.format(x=i)]))
                                        if preset_dict.has_key('keyframes'):                                    
                                            pdict[preset_dict['value'][0]['exprEval']] = i
                                        else:
                                            pdict[preset_dict['value']] = i

                                    new_ip = [a for a in pdict.keys() if a not in ropdict.keys()]
                                    dup_ip = list(set(ropdict.keys()) & set(pdict.keys()))
        
                                    rop.parm('vm_numaux').set(len(new_ip+ropdict.keys()))

                                    for aov in (new_ip+ropdict.keys()):
                                        #append new image planes                          
                                        if aov in new_ip:
                                            for parm in ipp:
                                                #unload parm dict
                                                parm_dict = json.loads(json.dumps(data[parm.name().replace('#', '{x}'.format(x = pdict[aov]))]))                                           
                                                
                                                #no keyframe check
                                                if not parm_dict.has_key('keyframes'):
                                                    rop.parm(parm.name().replace('#', '{x}'.format(x = len(ropdict) + new_ip.index(aov) + 1))).set(parm_dict['value'])
                                                else:
                                                    #keyframe / expression mode
                                                    key_list = parm_dict['value']
                                                    keys_to_add = genKeyframes(key_list)                                                                                                
                                                    rop.parm(parm.name().replace('#', '{x}'.format(x = len(ropdict) + new_ip.index(aov) + 1))).setKeyframes(tuple(keys_to_add))
                                        
                                        #merge based on priority
                                        elif aov in dup_ip:
                                            if behavior == 0:
                                                for parm in ipp:
                                                    #unload parm dict
                                                    parm_dict = json.loads(json.dumps(data[parm.name().replace('#', '{x}'.format(x = pdict[aov]))]))
                                                    if not parm_dict.has_key('keyframes'):
                                                        rop.parm(parm.name().replace('#', '{x}'.format(x = ropdict[aov]))).setExpression('')
                                                        rop.parm(parm.name().replace('#', '{x}'.format(x = ropdict[aov]))).deleteAllKeyframes()
                                                        rop.parm(parm.name().replace('#', '{x}'.format(x = ropdict[aov]))).set(parm_dict['value'])
                                                    else:
                                                        key_list = parm_dict['value']
                                                        keys_to_add = genKeyframes(key_list)                                                    
                                                        rop.parm(parm.name().replace('#', '{x}'.format(x = ropdict[aov]))).setKeyframes(tuple(keys_to_add))
                                else:
                                    default = True
                            rop.cook(force=True)
                    
                #replace mode - default = True
                if default:
                    for rop in s:
                        if rop.type().name() == 'ifd': 
                            #init vm_numaux
                            rop.parm('vm_numaux').set(data['vm_numaux']['value'])                        
                            for k in data:
                                parm_dict = json.loads(json.dumps(data[k]))
                                if k != 'vm_numaux' and k != 'ms_aovPreset':
                                    if not parm_dict.has_key('keyframes'):
                                        rop.parm(k).set(parm_dict['value'])
                                    else:
                                        key_list = parm_dict['value']
                                        keys_to_add = genKeyframes(key_list)
                                        rop.parm(k).setKeyframes(tuple(keys_to_add))
                        rop.cook(force=True)

            #missing ms_aov key
            else:
                hou.ui.displayMessage('Invalid Preset File')

        #failing os.isfile()
        else:
            hou.ui.displayMessage('Invalid Preset File')

    #no selection
    else:
        hou.ui.displayMessage('Select at least one node')
    
aovPresetLoad()
