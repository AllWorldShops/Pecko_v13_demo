/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        console.log("Add a Line");
        console.log("resModel:", this.props.list._config.resModel);
        // Check the user's group permissions asynchronously
        onWillStart(async () => {
            this.isAddLineGroup = await user.hasGroup("picking_create_lines.add_line_access_group");
        });

        // Store the model name
        this.modelName = this.props.list._config.resModel;
    },

    get displayRowCreates() {
        // If the model is 'stock.move' or 'stock.move.line', check the group
        if (this.modelName === "stock.move" || this.modelName === "stock.move.line") {
            return this.isAddLineGroup && this.isX2Many && this.canCreate; // Show 'Add a Line' only if group check passes
        }
        // For other models, no group check is needed, just check if X2Many and create permissions are valid
        return this.isX2Many && this.canCreate;
    },
});


