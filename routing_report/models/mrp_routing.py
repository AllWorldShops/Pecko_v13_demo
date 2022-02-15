from odoo import fields, models, api, _


class MrpRouting(models.Model):
    _inherit = "mrp.routing"
    
    def get_line_items(self):
        line_items = []
        notes = []
        for line in self.operation_ids:
            # if not line.note:
            # print(line[0], line[1], "lineeee")
            line_items.append(line)
            if line.note:
                print(line.name, "ppppppttttttt")
                line_items.append(line)
        print(len(line_items), line_items, "line_itemfllss")
        return line_items