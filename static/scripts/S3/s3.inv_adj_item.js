/**
 * Used by the inv/adj/adj_item controller
 * - Validate the Bin Quantities
 * - @ToDo: Show/Hide fields based on Reason
 */

$(document).ready(function() {
    var availableQuantity,
        binQuantity,
        binnedQuantity = S3.supply.binnedQuantity || 0,
        error,
        inlineComponent = $('#sub-defaultbin'),
        editBinBtnOK = $('#rdy-defaultbin-0'),
        newBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_none'),
        oldBinQuantityField = $('#sub_defaultbin_defaultbin_i_quantity_edit_0'),
        totalQuantityField = $('#inv_adj_item_new_quantity'),
        totalQuantity = totalQuantityField.val(),
        form = totalQuantityField.closest('form'),
        $this;

    if (totalQuantity) {
        totalQuantity = parseFloat(totalQuantity);
    } else {
        totalQuantity = S3.supply.oldQuantity || 0;
    }

    form.on('submit.s3', function(event) {
        if (!totalQuantityField.val()) {
            // Empty 'Revised Quantity' will give a server-side validation error
            // - this means we lose any revised bin allocations
            // => Catch this client-side instead
            event.preventDefault();
            // @ToDo: i18n
            message = 'Enter a number greater than or equal to 0';
            error = $('<div id="inv_adj_item_new_quantity-error" class="alert alert-error" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            totalQuantityField.parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    // Attach to the top-level element to catch newly-created readRows
    inlineComponent.on('click.s3', '.inline-edt', function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        // Make this Bin's Quantity available
        binnedQuantity = binnedQuantity - binQuantity;
    });

    editBinBtnOK.click(function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        // Make this Bin's Quantity unavailable
        binnedQuantity = binnedQuantity + binQuantity;
        // Validate the new bin again
        newBinQuantityField.change();
    });

    totalQuantityField.change(function() {
        totalQuantity = totalQuantityField.val();
        if (totalQuantity) {
            totalQuantity = parseFloat(totalQuantity);
            // Cleanup any old error message
            $('#inv_adj_item_new_quantity-error').remove();
        } else {
            totalQuantity = S3.supply.oldQuantity || 0;
        }
        if (totalQuantity < binnedQuantity) {
            // @ToDo: i18n
            message = 'Total Quantity increased to Quantity in Bins';
            error = $('<div id="inv_adj_item_new_quantity-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            totalQuantityField.val(binnedQuantity)
                              .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
        // Validate the new bin again
        newBinQuantityField.change();
    });

    newBinQuantityField.change(function() {
        binQuantity = newBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (binQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Bin Quantity reduced to Available Quantity';
            error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_none-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            newBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    oldBinQuantityField.change(function() {
        binQuantity = oldBinQuantityField.val();
        if (binQuantity) {
            binQuantity = parseFloat(binQuantity);
        } else {
            binQuantity = 0;
        }
        availableQuantity = totalQuantity - binnedQuantity;
        if (binQuantity > availableQuantity) {
            // @ToDo: i18n
            message = 'Bin Quantity reduced to Available Quantity';
            error = $('<div id="sub_defaultbin_defaultbin_i_quantity_edit_0-warning" class="alert alert-warning" style="padding-left:36px;">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');
            oldBinQuantityField.val(availableQuantity)
                               .parent().append(error).undelegate('.s3').delegate('.alert', 'click.s3', function() {
                $(this).fadeOut('slow').remove();
                return false;
            });
        }
    });

    inlineComponent.on('rowAdded', function(event, row) {
        // Make Quantity unavailable
        binnedQuantity = binnedQuantity + parseFloat(row.quantity.value);
        // Cleanup any old warning message
        $('#sub_defaultbin_defaultbin_i_quantity_edit_none-warning').remove();
    });

    inlineComponent.on('rowRemoved', function(event, row) {
        // Make Quantity available
        binnedQuantity = binnedQuantity - parseFloat(row.quantity.value);
    });

});