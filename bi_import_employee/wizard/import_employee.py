# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import io
import xlrd
import babel
import logging
import tempfile
import binascii
from io import StringIO
from datetime import date, datetime, time
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, UserError, ValidationError
_logger = logging.getLogger(__name__)

try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')


class ImportProducts(models.TransientModel):
	_name = 'import.products'
	_description = 'Import Products'

	file_type = fields.Selection([('CSV', 'CSV File'),('XLS', 'XLS File')],string='File Type', default='CSV')
	file = fields.Binary(string="Upload File")

	def import_products(self):
		if not self.file:
			raise ValidationError(_("Please Upload File to Import Products !"))

		if self.file_type == 'CSV':
			line = keys = ['default_code', 'uom_id', 'name', 'x_studio_field_qr3ai','x_studio_field_mHzKJ',
                  'standard_price','min_qty','pname','uom_po_id','currency_id',
                  'price', 'delay', 'route_ids', 'categ_id']
			try:
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise ValidationError(_("Please Select Valid File Format !"))
				
			values = {}
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						res = self.create_products(values)
		else:
			try:
				file = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				file.write(binascii.a2b_base64(self.file))
				file.seek(0)
				values = {}
				workbook = xlrd.open_workbook(file.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise ValidationError(_("Please Select Valid File Format !"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					values.update( {
							# 'name':line[0],
							# 'job_title': line[1],
							# 'mobile_phone': line[2],
							# 'work_phone':line[3],
							# 'work_email':line[4],
							# 'department_id':line[5],
							# 'address_id':line[6],
							# 'gender':line[7],
							# 'birthday':line[8],
							'default_code': line[0],
       						'uom_id': line[1],
							'name': line[2],
       						'x_studio_field_qr3ai': line[3],
             				'x_studio_field_mHzKJ': line[4],
                  			'standard_price': line[5],
                  			'min_qty':line[6],
							'pname':line[7],
       						'uom_po_id':line[8],
             				'currency_id':line[9],
                  			'price': line[10],
                     		'delay': line[11],
                       		'route_ids': line[12],
                         	'categ_id': line[13]
							})
					res = self.create_products(values)
    
	def create_products(self, values):
		products = self.env['product.product']
        # birthday = self.get_birthday(values.get('birthday')
		seller_lines = []
		name = self.env['res.partner'].search([('name', '=', values.get('pname'))], limit=1)
		ac_receivable = self.env['account.account'].search([('internal_type', '=', 'receivable'),('deprecated','=', False)], limit=1)
		ac_payable = self.env['account.account'].search([('internal_type', '=', 'payable'),('deprecated','=', False)], limit=1)

		if not name:
			name.create({
				'name': str(values.get('pname')),
				'property_account_receivable_id': ac_receivable.id,
				'property_account_payable_id': ac_payable.id,
				})
			return name
		# print(name, "////name>>>>>>>>>>>>>>>", len(name))
		currency = self.env['res.currency'].search([('name', '=', values.get('currency_id')),('active', '=', True)], limit=1)
		bc_currency = self.env['res.currency'].search([('active', '=', True)], limit=1)
		if not currency:
			currency = bc_currency
			# return currency
		seller_lines.append((0, 0,{
			'min_qty': values.get('min_qty'),
            'name': name.id,
            'currency_id': currency.id,
            'price': values.get('price'),
            'delay': values.get('delay'),
		}))
		uom = self.env['uom.uom'].search([('name', '=', values.get('uom_id'))], limit=1)
		uom_category = self.env['uom.uom'].search([], limit=1)
		if not uom:
			uom.create({
				'name': str(values.get('uom_id')),
				'category_id': uom_category.id,
				'uom_type': 'bigger',
				})
			return uom


		product_categ = self.env['product.category'].search([('name', '=', values.get('categ_id'))], limit=1)
		if not product_categ:
			product_categ.create({
				'name': str(values.get('categ_id'))
				})
			return product_categ

		# birthday = self.get_birthday(values.get('birthday'))
		vals = {
				# 'name' : values.get('name'),
				# 'job_title' : values.get('job_title'),
				# 'mobile_phone' : values.get('mobile_phone'),
				# 'work_phone' : values.get('work_phone'),
				# 'work_email' : values.get('work_email'),
				# 'department_id' : department_id.id,
				# 'address_id' : address_id.id,
				# 'gender' : gender,
				# 'birthday' : birthday,
    
				'default_code': values.get('default_code'),
				'uom_id': uom.id,
				'name': values.get('name'),
				'x_studio_field_qr3ai': values.get('x_studio_field_qr3ai'),
				'x_studio_field_mHzKJ': values.get('x_studio_field_mHzKJ'),
				'standard_price': values.get('standard_price'),
				'seller_ids': seller_lines,
				# 'seller_ids.name':values.get('seller_ids.name'),
				'uom_po_id': uom.id,
				# 'seller_ids.currency_id':values.get('seller_ids.currency_id'),
				# 'seller_ids.price': values.get('seller_ids.price'),
				# 'seller_ids.delay': values.get('seller_ids.delay'),
				# 'route_ids': 1,
				'categ_id': product_categ.id,
				}


		# if values.get('name')=='':
		# 	raise Warning(_('Employee Name is Required !'))
		# if values.get('department_id')=='':
		# 	raise Warning(_('Department Field can not be Empty !'))

		res = products.create(vals)
		return res


	# def get_department(self, name):
	# 	department = self.env['hr.department'].search([('name', '=', name)],limit=1)
	# 	if department:
	# 		return department
	# 	else:
	# 		raise UserError(_('"%s" Department is not found in system !') % name)

	# def get_address(self, name):
	# 	address = self.env['res.partner'].search([('name', '=', name)],limit=1)
	# 	if address:
	# 		return address
	# 	else:
	# 		raise UserError(_('"%s" Address is not found in system !') % name)

	# def get_birthday(self, date):
	# 	try:
	# 		birthday = datetime.strptime(date, '%Y/%m/%d')
	# 		return birthday
	# 	except Exception:
	# 		raise ValidationError(_('Wrong Date Format ! Date Should be in format YYYY/MM/DD'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: