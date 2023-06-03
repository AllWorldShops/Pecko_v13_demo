odoo.define('picking_create_lines.add_groups_one2many_add_line', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');
    
            ListRenderer.include({

            init: function (parent, state, params) {
                var self = this;
                this._super.apply(this, arguments);
                this.getSession().user_has_group('picking_create_lines.add_line_access_group'
                ).then(function(has_group) {
                if (!has_group) {
            
                
                    if ((state.model === "stock.move" && parent.name === "move_ids_without_package"
                    ) || (state.model === "stock.move.line" && parent.name === "move_line_ids_without_package") ) {
                        self.addCreateLine = false;
                    }
                    
                   }
                });
                    
                }, 
                });
            });
