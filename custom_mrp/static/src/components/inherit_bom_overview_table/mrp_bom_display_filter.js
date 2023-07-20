odoo.define('web.mrp_bom_display_filter', function (require) {
"use strict";

const { BomOverviewComponent } = require ("@mrp/components/bom_overview/mrp_bom_overview");
const { patch }  = require ("@web/core/utils/patch");
const { Component, useState } = owl;
console.log(BomOverviewComponent,'BomOverviewComponent');

patch(BomOverviewComponent.prototype, 'mrp_costs',{
   setup() {
   this._super.apply();
        this.state.showOptions.costs = false
    }
    });
});