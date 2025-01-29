from odoo import models, fields


class UomLog(models.Model):
    _name = 'uom.uom'
    _inherit = ['mail.thread', 'uom.uom', 'mail.activity.mixin']

    name = fields.Char('Unit of Measure', tracking=True, required=True, translate=True)
    category_id = fields.Many2one(
        'uom.category', 'Category', required=True, ondelete='cascade', tracking=True,
        help="Conversion between Units of Measure can only occur if they belong to the same category. The conversion will be made based on the ratios.")
    uom_type = fields.Selection([
        ('bigger', 'Bigger than the reference Unit of Measure'),
        ('reference', 'Reference Unit of Measure for this category'),
        ('smaller', 'Smaller than the reference Unit of Measure')], 'Type',
        default='reference', tracking=True, required=1)
    factor_inv = fields.Float(
        'Bigger Ratio', compute='_compute_factor_inv', digits=0,  # force NUMERIC with unlimited precision
        readonly=True, required=True, tracking=True,
        help='How many times this Unit of Measure is bigger than the reference Unit of Measure in this category: 1 * (this unit) = ratio * (reference unit)')
    active = fields.Boolean('Active', default=True, tracking=True, help="Uncheck the active field to disable a unit of measure without deleting it.")
    rounding = fields.Float(
        'Rounding Precision', default=0.01, digits=0, required=True, tracking=True,
        help="The computed quantity will be a multiple of this value. "
             "Use 1.0 for a Unit of Measure that cannot be further split, such as a piece.")





