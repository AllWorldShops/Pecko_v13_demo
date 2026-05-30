from odoo import fields


def post_init_hook(env):
    """
    Creates the daily cron job after all models are registered.
    The cron runs every day but the Python method only generates
    the report when today is the last day of the month.
    """
    IrCron = env['ir.cron']
    IrModel = env['ir.model']

    # Avoid duplicate on module upgrade
    existing = IrCron.search(
        [('name', '=', 'Generate Monthly Stock Inventory Report')], limit=1
    )
    if existing:
        # Ensure it stays daily (in case of upgrade from old monthly config)
        existing.write({'interval_number': 1, 'interval_type': 'days'})
        return

    model = IrModel.search([('model', '=', 'audit.monthly.report')], limit=1)
    if not model:
        return

    IrCron.create({
        'name':             'Generate Monthly Stock Inventory Report',
        'model_id':         model.id,
        'state':            'code',
        'code':             'model.cron_generate_monthly_report()',
        'interval_number':  1,
        'interval_type':    'days',
        'numbercall':       -1,
        'active':           True,
        'nextcall':         fields.Datetime.now(),
        'user_id':          env.ref('base.user_root').id,
    })
