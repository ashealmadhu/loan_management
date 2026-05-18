/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";

patch(FormController.prototype, {
    /**
     * Override save to provide a custom toast notification for the image field requirement.
     */
    async save() {
        if (this.model.root.resModel === "dev.loan.type") {
            const record = this.model.root;
            if (!record.data.image) {
                this.env.services.notification.add(_t("Image field is required"), {
                    type: "danger",
                });
                return false;
            }
        }
        return await super.save(...arguments);
    },
});
