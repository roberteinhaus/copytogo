drives = [];

function setStatusText() {
    var count = 0;
    var size = 0;
    var drive = drives[jQuery("#usbdrive option:selected").val()];
    var files = getSelectedFiles();

    jQuery.each(files, function(index, file) {
        count++;
        size += parseInt(file.size);
    });
    size = Math.ceil(size / 1048576);

    var free = 0;
    if (jQuery("#erase").is(":checked")) {
        free = drive.size;
    }
    else {
        free = drive.free
    }

    jQuery("#status").text(count + ' files (' + size + ' MB) - Free: ' + Math.floor(free/1024 - size) + ' / ' + Math.floor(drive.size/1024) + ' MB');
}

function getSelectedFiles() {
    var files = [];
    var selected_nodes = jQuery('#jstree').jstree("get_selected");
    jQuery.each(selected_nodes, function(index, nodeid) {
        node = jQuery('#jstree').jstree(true).get_node(nodeid);
        if(node.type == 'file') {
            files.push(node.original);
        }
    });
    return files;
}

function getUSBDrives() {
    jQuery.getJSON("/usbdrives", null, function(data) {
        jQuery("#usbdrive option").remove();
        jQuery.each(data, function(index, drive) {
            jQuery("#usbdrive").append(
                jQuery("<option></option>")
                .text((drive.label || drive.name) + ' (' + drive.name + ') - Free: ' + Math.floor(drive.free/1024) + ' / ' + Math.floor(drive.size/1024) + ' MB')
                .val(index)
            );
        });
        drives = data;
        setStatusText();
    });
}

jQuery( document ).ready(function() {
    jQuery('#jstree').jstree({
        'core' : {
            'data' : {
                'url' : 'dirtree',
                'dataType' : 'json'
            },
            'themes' : {
                'name' : 'proton',
                'responsive' : true,
                'variant' : 'large'
            }
        },
        'types' : {
            'root' : {
                'icon' : 'fa fa-lg fa-asterisk'
            },
            'directory' : {
                'icon' : 'fa fa-lg fa-folder'
            },
            'file' : {
                'icon' : 'fa fa-lg fa-file'
            }
        },
        'plugins' : [ 'checkbox', 'sort', 'wholerow', 'types' ]
    });

    jQuery('#jstree').on("changed.jstree", function () {
        setStatusText();
    });

    jQuery('#erase').change(function() {
        setStatusText();
    });

    jQuery("#usbdrive").change(function() {
        setStatusText();
    });

    jQuery('#copyYes').click(function() {
        var nodes = getSelectedFiles();
        var files = [];
        jQuery.each(nodes, function(index, file) {
            files.push(file.path);
        });
        var req = {};
        var drive = drives[jQuery("#usbdrive option:selected").val()];
        req.drive = drive.name;
        req.erase = jQuery('#erase').is(':checked');
        req.files = files
        jQuery.post('/copy', JSON.stringify(req), function() {
            getUSBDrives();
            jQuery('#jstree').jstree('deselect_all');
            jQuery('#jstree').jstree('close_all');
            jQuery('#jstree').jstree('open_node', jQuery('#j1_1'));
            jQuery('#loading').modal('toggle');
        });
    });

    getUSBDrives();
});
