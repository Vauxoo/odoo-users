# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012
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

from openerp import api, models, tools
from lxml import etree
import re


class MergeFuseWizard(models.TransientModel):
    _name = 'merge.fuse.wizard'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        result = super(MergeFuseWizard, self).fields_view_get(cr, uid,
                                                              view_id,
                                                              view_type,
                                                              context,
                                                              toolbar,
                                                              submenu)
        if context.get('merge_fuse_object'):
            merge_object = self.pool.get('merge.object')
            fuse_data = merge_object.browse(cr, uid,
                                            context.get('merge_fuse_object'),
                                            context)
            all_fields = {}
            xml_form = etree.Element('form',
                                     {'string':
                                      tools.ustr(fuse_data.name)})
            etree.SubElement(xml_form, 'group', {'colspan': '4'})
            etree.SubElement(xml_form,
                             'separator',
                             {'string': 'About to consolidate '
                              'the selected records in one',
                              'colspan': '6'})
            # TODO Creating a tree with the selected records,
            # allowing to select which record will be the main
            xml_group3 = etree.SubElement(xml_form,
                                          'group',
                                          {'col': '2',
                                           'colspan': '4'})
            etree.SubElement(xml_group3,
                             'button',
                             {'string': 'Close',
                              'icon': "gtk-close",
                              'special': 'cancel'})
            etree.SubElement(xml_group3,
                             'button',
                             {'string': 'Apply',
                              'icon': "gtk-execute",
                              'type': 'object',
                              'name': "action_apply"})
            root = xml_form.getroottree()
            result['arch'] = etree.tostring(root)
            result['fields'] = all_fields
        return result

    @api.multi
    def merge_records(self, table, main_id, old_ids, orm_model):
        """Method used to merge records in all tables with
        a reference to the objects to merge
        @param tabel: Table name of the records to merge. i.e. res_users
        @type tabel: str or unicode
        @param main_id: Id of the main record, this id will replace the other
                        ids in the tables related
        @type main_id: integer
        @param old_ids: List  with the ids of the records to merge
        @type old_ids: list or tuple
        @param orm_model: Name of the model for the orm. i.e. res.users
        @type orm_model: str or unicode
        """

        self._cr.execute('''
DROP FUNCTION IF EXISTS merge_records(model varchar, main_id integer,
                                      old_ids integer[], orm_model varchar);
CREATE OR REPLACE FUNCTION merge_records(model varchar, main_id integer,
                                         old_ids integer[], orm_model varchar)
RETURNS float AS $$
    DECLARE

        value_table varchar;
        value_column varchar;
        values RECORD;
        proper_id integer;
        record_id integer;
        amount float;
    BEGIN
        FOR value_table, value_column IN SELECT cl1.relname as table,
                             att1.attname as column
                      FROM pg_constraint as con, pg_class as cl1,
                           pg_class as cl2, pg_attribute as att1,
                           pg_attribute as att2
                      WHERE con.conrelid = cl1.oid
                           AND con.confrelid = cl2.oid
                           AND array_lower(con.conkey, 1) = 1
                           AND con.conkey[1] = att1.attnum
                           AND att1.attrelid = cl1.oid
                           AND cl2.relname = model
                           AND att2.attname = 'id'
                           AND array_lower(con.confkey, 1) = 1
                           AND con.confkey[1] = att2.attnum
                           AND att2.attrelid = cl2.oid
                           AND con.contype = 'f' LOOP
            FOREACH record_id SLICE 0 IN ARRAY old_ids LOOP
                proper_id := (SELECT id
                              FROM ir_property
                              WHERE res_id = orm_model|| ',' ||
                                             record_id LIMIT 1);
                IF proper_id is not null THEN
                    UPDATE ir_property
                    SET res_id = orm_model|| ',' || main_id
                    WHERE res_id = orm_model|| ',' || record_id    ;
                END IF;
                proper_id := (SELECT id
                            FROM ir_property
                            WHERE value_reference = orm_model|| ',' ||
                                    record_id LIMIT 1);
                IF proper_id is not null THEN
                    UPDATE ir_property
                    SET value_reference = orm_model|| ',' || main_id
                    WHERE value_reference = orm_model|| ',' || record_id;
                END IF;
                BEGIN
                    EXECUTE 'UPDATE ' || value_table ||
                            ' SET ' || value_column || ' = ' || main_id ||
                            ' WHERE ' || value_column || ' = '
                                || record_id;
                EXCEPTION WHEN unique_violation THEN
                    -- Ignore duplicate inserts.
                END;
            END LOOP;
        END LOOP;
        RETURN amount; END;
    $$ LANGUAGE plpgsql;''')
        old_ids_str = re.sub(r'^(\(|\[)', '{', str(old_ids))
        old_ids_str = re.sub(r'(\)|\])$', '}', old_ids_str)

        self._cr.execute('SELECT merge_records(CAST(%s AS varchar),'
                         '%s, %s, CAST(%s AS varchar))',
                         (table, main_id, old_ids_str, orm_model))

    @api.multi
    def action_apply(self):
        return {'type': 'ir.actions.act_window_close'}


class MergeEditingWizard(models.TransientModel):
    _name = 'merge.editing.wizard'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        result = super(MergeEditingWizard, self).fields_view_get(cr, uid,
                                                                 view_id,
                                                                 view_type,
                                                                 context,
                                                                 toolbar,
                                                                 submenu)
        if context.get('merge_editing_object'):
            merge_object = self.pool.get('merge.object')
            editing_data = merge_object.\
                browse(cr, uid,
                       context.get('merge_editing_object'), context)
            all_fields = {}
            xml_form = etree.Element('form', {'string':
                                              tools.ustr(editing_data.name)})
            xml_group = etree.SubElement(xml_form, 'group', {'colspan': '4'})
            etree.SubElement(xml_group, 'field',
                             {'name': 'serpent_image',
                              'nolabel': '1',
                              'colspan':
                              '1', 'modifiers':
                              '{"readonly": true}',
                              'widget': 'image'})
            etree.SubElement(xml_group, 'label',
                             {'string': '', 'colspan': '2'})
            all_fields['serpent_image'] = {'type': 'binary',
                                           'string': ''}
            xml_group = etree.SubElement(xml_form, 'group', {'colspan': '4'})
            model_obj = self.pool.get(context.get('active_model'))
            for field in editing_data.field_ids:
                if field.ttype == "many2many":
                    field_info = model_obj.fields_get(cr, uid, [field.name],
                                                      context)
                    all_fields[field.name] = field_info[field.name]
                    all_fields["selection_" + field.name] = \
                        {'type': 'selection',
                         'string': field_info[field.name]['string'],
                         'selection': [('set', 'Set'),
                                       ('remove_m2m', 'Remove'),
                                       ('add', 'Add')]}
                    xml_group = etree.SubElement(xml_group, 'group',
                                                 {'colspan': '4'})
                    etree.\
                        SubElement(xml_group,
                                   'separator',
                                   {'string': field_info[field.name]['string'],
                                    'colspan': '2'})
                    etree.SubElement(xml_group,
                                     'field',
                                     {'name': "selection_" + field.name,
                                      'colspan': '2',
                                      'nolabel': '1'})
                    etree.SubElement(xml_group,
                                     'field',
                                     {'name': field.name,
                                      'colspan': '4',
                                      'nolabel': '1',
                                      'attrs': "{'invisible':[('selection_" +
                                      field.name + "','=','remove_m2m')]}"})
                elif field.ttype == "many2one":
                    field_info = model_obj.fields_get(cr, uid, [field.name],
                                                      context)
                    if field_info:
                        all_fields[
                            "selection_" +
                            field.name] = {
                            'type': 'selection',
                            'string': field_info[
                                field.name]['string'],
                            'selection': [
                                ('set',
                                 'Set'),
                                ('remove',
                                 'Remove')]}
                        all_fields[
                            field.name] = {
                            'type': field.ttype,
                            'string': field.field_description,
                            'relation': field.relation}
                        etree.SubElement(xml_group,
                                         'field',
                                         {'name': "selection_" + field.name,
                                          'colspan': '2'})
                        etree.SubElement(
                            xml_group,
                            'field',
                            {
                                'name': field.name,
                                'nolabel': '1',
                                'colspan': '2',
                                'attrs': "{'invisible':[('selection_" +
                                field.name + "','=','remove')]}"})
                elif field.ttype == "char":
                    field_info = model_obj.fields_get(cr, uid, [field.name],
                                                      context)
                    all_fields[
                        "selection_" +
                        field.name] = {
                        'type': 'selection',
                        'string': field_info[
                            field.name]['string'],
                        'selection': [
                            ('set',
                             'Set'),
                            ('remove',
                             'Remove')]}
                    all_fields[
                        field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'size': field.size or 256}
                    etree.SubElement(
                        xml_group, 'field', {
                            'name': "selection_" +
                            field.name,
                            'colspan': '2'})
                    etree.SubElement(
                        xml_group,
                        'field',
                        {
                            'name': field.name,
                            'nolabel': '1',
                            'attrs': "{'invisible':[('selection_" +
                            field.name + "','=','remove')]}",
                            'colspan': '2'})
                elif field.ttype == 'selection':
                    field_info = model_obj.fields_get(
                        cr, uid, [
                            field.name], context)
                    all_fields[
                        "selection_" +
                        field.name] = {
                        'type': 'selection',
                        'string': field_info[
                            field.name]['string'],
                        'selection': [
                            ('set',
                             'Set'),
                            ('remove',
                             'Remove')]}
                    field_info = model_obj.fields_get(
                        cr, uid, [
                            field.name], context)
                    etree.SubElement(
                        xml_group, 'field', {
                            'name': "selection_" + field.name, 'colspan': '2'})
                    etree.SubElement(
                        xml_group,
                        'field',
                        {
                            'name': field.name,
                            'nolabel': '1',
                            'colspan': '2',
                            'attrs': "{'invisible':[('selection_" +
                            field.name + "','=','remove')]}"})
                    all_fields[
                        field.name] = {
                        'type': field.ttype,
                        'string': field.field_description,
                        'selection': field_info[
                            field.name]['selection']}
                else:
                    field_info = model_obj.fields_get(
                        cr, uid, [
                            field.name], context)
                    all_fields[
                        field.name] = {
                        'type': field.ttype,
                        'string': field.field_description}
                    all_fields[
                        "selection_" +
                        field.name] = {
                        'type': 'selection',
                        'string': field_info[
                            field.name]['string'],
                        'selection': [
                            ('set',
                             'Set'),
                            ('remove',
                             'Remove')]}
                    if field.ttype == 'text':
                        xml_group = etree.SubElement(
                            xml_group, 'group', {
                                'colspan': '6'})
                        etree.SubElement(
                            xml_group, 'separator', {
                                'string': all_fields[
                                    field.name]['string'], 'colspan': '2'})
                        etree.SubElement(
                            xml_group, 'field', {
                                'name': "selection_" + field.name,
                                'colspan': '2',
                                'nolabel': '1'})
                        etree.SubElement(
                            xml_group,
                            'field',
                            {
                                'name': field.name,
                                'colspan': '4',
                                'nolabel': '1',
                                'attrs': "{'invisible':[('selection_" +
                                field.name + "','=','remove')]}"})
                    else:
                        all_fields[
                            "selection_" +
                            field.name] = {
                            'type': 'selection',
                            'string': field_info[
                                field.name]['string'],
                            'selection': [
                                ('set',
                                 'Set'),
                                ('remove',
                                 'Remove')]}
                        etree.SubElement(
                            xml_group, 'field', {
                                'name': "selection_" +
                                field.name,
                                'colspan': '2', })
                        etree.SubElement(
                            xml_group,
                            'field',
                            {
                                'name': field.name,
                                'nolabel': '1',
                                'attrs': "{'invisible':[('selection_" +
                                field.name + "','=','remove')]}",
                                'colspan': '2',
                            })

            etree.SubElement(
                xml_form, 'separator', {
                    'string': '', 'colspan': '6'})
            xml_group3 = etree.SubElement(
                xml_form, 'group', {
                    'col': '2', 'colspan': '4'})
            etree.SubElement(
                xml_group3, 'button', {
                    'string': 'Close',
                    'icon': "gtk-close",
                    'special': 'cancel'})
            etree.SubElement(xml_group3,
                             'button',
                             {'string': 'Apply',
                              'icon': "gtk-execute",
                              'type': 'object',
                              'name': "action_apply"})

            root = xml_form.getroottree()
            result['arch'] = etree.tostring(root)
            result['fields'] = all_fields
        return result

    def create(self, cr, uid, vals, context=None):
        if context.get('active_model') and context.get('active_ids'):
            model_obj = self.pool.get(context.get('active_model'))
            dict_cr = {}
            for key, val in vals.items():
                if key.startswith('selection_'):
                    split_key = key.split('_', 1)[1]
                    if val == 'set':
                        dict_cr.update({split_key: vals.get(split_key, False)})
                    elif val == 'remove':
                        dict_cr.update({split_key: False})
                    elif val == 'remove_m2m':
                        dict_cr.update({split_key: [(5, 0, [])]})
                    elif val == 'add':
                        m2m_list = []
                        for m2m_id in vals.get(split_key, False)[0][2]:
                            m2m_list.append((4, m2m_id))
                        dict_cr.update({split_key: m2m_list})
            if dict_cr:
                model_obj.write(
                    cr,
                    uid,
                    context.get('active_ids'),
                    dict_cr,
                    context)
        result = super(MergeEditingWizard, self).create(cr, uid, {}, context)
        return result

    @api.multi
    def action_apply(self):
        return {'type': 'ir.actions.act_window_close'}
