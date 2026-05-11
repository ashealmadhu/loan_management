/** @odoo-module **/

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

const userMenuRegistry = registry.category("user_menuitems");


    userMenuRegistry.remove("documentation");
        userMenuRegistry.remove("support");
        userMenuRegistry.remove("shortcuts");
        userMenuRegistry.remove("web_tour.tour_enabled");
        userMenuRegistry.remove("separator");
        userMenuRegistry.remove("odoo_account");


        userMenuRegistry.remove("install_pwa");
userMenuRegistry.remove("shortcuts");



userMenuRegistry.add("user_name_display", (env) => {
    const userName = user.name || "User";
    return {
        type: "item",
        id: "user_name_display",
        description: `${userName}`,
        callback: () => {},
        sequence: 30,
    };
});
