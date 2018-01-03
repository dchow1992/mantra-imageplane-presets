import json
def aovPresetSave():
    s = hou.selectedNodes()
    if len(s) == 1:
        s = s[0]
        if s.type().name() == 'ifd':
            default_dir = '/home/dchow/scripts/json_temp/'
            outfile = hou.ui.selectFile(start_directory=default_dir, title='Save Preset As', pattern='*.json', chooser_mode=hou.fileChooserMode.Write)
            if outfile != '':
                if outfile.split('.')[-1] != 'json':
                    outfile += '.json'
            data = {}

            #extra image planes rop tab parm templates
            p = [a for a in s.parmTemplateGroup().findFolder('Images').parmTemplates() if a.label() == 'Extra Image Planes'][0].parmTemplates()

            #quickplane parms
            qpp = list(s.parmsInFolder(('Images', 'Extra Image Planes')))

            #src img plane parms
            ipp = s.parm('vm_numaux').multiParmInstances()

            #this list will hold all the parm objects to use as keys in our json file, except for our ms_aovPreset custom key
            parmTemplateList = []

            parmTemplateList.append(s.parm('vm_exportcomponents'))

            parmTemplateList += qpp

            parmTemplateList.append(s.parm('vm_numaux'))

            parmTemplateList += list(s.parm('vm_numaux').multiParmInstances()) 

            #fill up our dictionary
            data['ms_aovPreset'] = 1
            for parm in parmTemplateList:
                parm_dict = {}               

                #if keyframed or has expression
                if len(parm.keyframes()) > 0:
                    parm_dict['keyframes'] = 1
                    #if expression
                    if parm.parmTemplate().type() == hou.parmTemplateType.String:
                        key_list = []
                        for k in parm.keyframes():                                
                            key_dict = {}
                            key_dict['t'] = k.time()
                            key_dict['expr'] = k.expression()
                            key_dict['lang'] = 'Hscript' if k.expressionLanguage() == hou.exprLanguage.Hscript else 'Python'
                            key_dict['type'] = 'StringKeyframe'
                            key_dict['exprEval'] = parm.eval()
                            key_list.append(key_dict)
                        parm_dict['value'] = key_list

                    else:
                        key_list = []
                        for k in parm.keyframes():
                            key_dict = {}
                            key_dict['t'] = k.time()
                            key_dict['expr'] = k.expression()
                            key_dict['lang'] = 'Hscript' if k.expressionLanguage() == hou.exprLanguage.Hscript else 'Python'
                            key_dict['v'] = k.value()
                            key_dict['s'] = k.slope()
                            key_dict['use_accel_ratio'] = 1 if k.isAccelInterpretedAsRatio() == True else 0
                            key_dict['exprEval'] = parm.eval()

                            if k.expression() != 'bezier()':
                                key_dict['a'] = k.accel()
                                key_dict['type'] = 'ChanRefKeyframe'
                            else:                                    
                                key_dict['auto_slopes'] = 1 if k.isSlopeAuto() == True else 0                                    
                                key_dict['out_a'] = k.accel()
                                key_dict['type'] = 'BezierKeyframe'
                                if len(parm.keyframes()) > 1:
                                    key_dict['in_a'] = k.inAccel() 

                            key_list.append(key_dict)
                        parm_dict['value'] = key_list

                #if string parm use unexpanded string
                elif parm.parmTemplate().type() == hou.parmTemplateType.String:
                    parm_dict['value'] = parm.unexpandedString() 
                else:
                    parm_dict['value'] = parm.eval()
                data[parm.name()] = parm_dict

            #data -> json
            with open(outfile, 'w') as x:
                json.dump(data, x, indent=4, separators=(',', ': '))
        else:
            hou.ui.displayMessage('Invalid node type')
    #no selection
    elif s == 0:
        hou.ui.displayMessage('Select at least one node')
    else:
        hou.ui.displayMessage('Select one node')

aovPresetSave()
