// load the xml files using ajax 08-09-22
odoo.define('custom_mrp.template_call_name_odoo', function (require) {
'use strict';
var core = require('web.core');
var ajax = require('web.ajax');
// call the customized mail template
var qweb = core.qweb;
ajax.loadXML('/custom_mrp/static/src/components/inherit_bom_overview_table/mrp_inherit_bom_overview_table.xml', qweb);
});