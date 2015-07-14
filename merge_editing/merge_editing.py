# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012
#    Serpent Consulting Services (<http://www.serpentcs.com>)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################


from openerp import models, fields, api, _
from openerp import osv


class merge_object(models.Model):
    _name = "merge.object"

    name = fields.Char("Name", size=64, required=True, select=1)
    model_id = fields.Many2one('ir.model', 'Model', required=True, select=1)
    field_ids = fields.Many2many('ir.model.fields', 'merge_field_rel',
                                 'merge_id', 'field_id', 'Fields')
    ref_ir_act_window = fields.Many2one('ir.actions.act_window',
                                        'Sidebar action', readonly=True,
                                        help="Sidebar action to make this "
                                        "template available on records "
                                        "of the related document model")
    ref_ir_value = fields.Many2one('ir.values', 'Sidebar button',
                                   readonly=True,
                                   help="Sidebar button to open the "
                                   "sidebar action")
    ref_ir_act_window_fuse = fields.Many2one('ir.actions.act_window',
                                             'Sidebar fuse action',
                                             readonly=True,
                                             help="Sidebar action to make "
                                             "this template available on "
                                             "records of the related "
                                             "document model")
    ref_ir_value_fuse = fields.Many2one('ir.values', 'Sidebar fuse button',
                                        readonly=True,
                                        help="Sidebar button to open "
                                        "the sidebar action")
    model_list = fields.Char('Model List', size=256)
    fuse = fields.boolean('fuse elements', required=False)

    @api.multi
    def onchange_model(self, model_id):
        model_list = ""
        if model_id:
            model_obj = self.env['ir.model']
            model_data = model_obj.browse(model_id)
            model_list = "[" + str(model_id) + ""
            active_model_obj = self.env[model_data.model]
            if active_model_obj._inherits:
                for key, val in active_model_obj._inherits.items():
                    model_ids = model_obj.search([('model', '=', key)])
                    if model_ids:
                        model_list += "," + str(model_ids._ids[0]) + ""
            model_list += "]"
        return {'value': {'model_list': model_list}}

    @api.one
    def create_action_fuse(self):
        vals = {}
        action_obj = self.env['ir.actions.act_window']
        src_obj = self.model_id.model
        button_name = _('Mass Fuse (%s)') % self.name
        vals['ref_ir_act_window_fuse'] = action_obj.create({
            'name': button_name,
            'type': 'ir.actions.act_window',
            'res_model': 'merge.fuse.wizard',
            'src_model': src_obj,
            'view_type': 'form',
            'context': "{'merge_fuse_object' : %d}" % (self.id),
            'view_mode': 'form,tree',
            'target': 'new',
            'auto_refresh': 1
        })
        vals['ref_ir_value_fuse'] = self.env['ir.values'].\
            create({
                'name': button_name,
                'model': src_obj,
                'key2': 'client_action_multi',
                'value': "ir.actions.act_window," +
                str(vals['ref_ir_act_window_fuse']),
                'object': True,
            })
        self.write({
            'ref_ir_act_window_fuse': vals.
            get('ref_ir_act_window_fuse', False),
            'ref_ir_value_fuse': vals.get('ref_ir_value_fuse', False),
        })

    @api.one
    def create_action(self):
        vals = {}
        action_obj = self.env['ir.actions.act_window']
        src_obj = self.model_id.model
        button_name = _('Mass Editing (%s)') % self.name
        vals['ref_ir_act_window'] = action_obj.create({
            'name': button_name,
            'type': 'ir.actions.act_window',
            'res_model': 'merge.editing.wizard',
            'src_model': src_obj,
            'view_type': 'form',
            'context': "{'merge_editing_object' : %d}" % (self.id),
            'view_mode': 'form,tree',
            'target': 'new',
            'auto_refresh': 1
        })
        vals['ref_ir_value'] = self.env['ir.values'].create({
            'name': button_name,
            'model': src_obj,
            'key2': 'client_action_multi',
            'value': "ir.actions.act_window," + str(vals['ref_ir_act_window']),
            'object': True,
            })
        self.write({
            'ref_ir_act_window': vals.
            get('ref_ir_act_window', False),
            'ref_ir_value': vals.
            get('ref_ir_value', False)
        })

    @api.one
    def unlink_action(self):
        try:
            if self.ref_ir_act_window:
                self.env['ir.actions.act_window'].\
                    unlink(self.ref_ir_act_window.id)
            if self.ref_ir_value:
                ir_values_obj = self.env['ir.values']
                ir_values_obj.unlink(self.ref_ir_value.id)
        except:
            raise osv.except_osv(_("Warning"),
                                 _("Deletion of the action record failed."))
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
