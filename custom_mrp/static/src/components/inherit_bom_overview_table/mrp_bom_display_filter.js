/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { BomOverviewDisplayFilter } from "@mrp/components/bom_overview_display_filter/mrp_bom_overview_display_filter";
const { Component } = owl;
import { patch } from "@web/core/utils/patch";
console.log(BomOverviewDisplayFilter,'BomOverviewDisplayFilter');

patch(BomOverviewDisplayFilter.prototype, "mrp_costs", {
    setup() {
        this._super.apply();
        this.displayOptions = {
            availabilities: this.env._t('Availabilities'),
            leadTimes: this.env._t('Lead Times'),
//            costs: ('Costs'),
            operations: this.env._t('Operations'),
        };
    },
});
BomOverviewDisplayFilter.props = {
    showOptions: {
        type: Object,
        shape: {
            availabilities: Boolean,
//            costs: Boolean,
            operations: Boolean,
            leadTimes: Boolean,
            uom: Boolean,
            attachments: Boolean,
        },
    },
    changeDisplay: Function,
};

