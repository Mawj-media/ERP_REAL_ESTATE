frappe.pages["bulk-import-payments"].on_page_load = function (wrapper) {
	frappe.breadcrumbs.add("Real Estate", "Bulk Import Payments");

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Bulk Import Payments"),
		single_column: true,
	});

	page.add_inner_button(__("Download Template"), function () {
		window.open(
			"/api/method/real_estate.real_estate.page.bulk_import_payments.bulk_import_payments.download_template"
		);
	});

	$(frappe.render_template("bulk_import_payments")).appendTo(page.body);

	page.body.addClass("no-border");

	let $upload_area = page.body.find(".import-upload-area");
	let $file_input = page.body.find(".import-file-input");
	let $preview_section = page.body.find(".import-preview-section");
	let $preview_table = page.body.find(".import-preview-table");
	let $preview_count = page.body.find(".import-preview-count");
	let $import_btn = page.body.find(".btn-import");
	let $result_section = page.body.find(".import-result-section");
	let $result_content = page.body.find(".import-result-content");
	let $drop_text = page.body.find(".drop-text");

	let uploaded_file_url = null;
	let dt_instance = null;

	$upload_area.on("click", function () {
		$file_input.click();
	});

	$file_input.on("click", function (e) {
		e.stopPropagation();
	});

	$upload_area.on("dragover", function (e) {
		e.preventDefault();
		e.stopPropagation();
		$upload_area.addClass("dragover");
		$drop_text.text(__("Drop CSV file here"));
	});

	$upload_area.on("dragleave", function (e) {
		e.preventDefault();
		e.stopPropagation();
		$upload_area.removeClass("dragover");
		$drop_text.text(__("Click to upload or drag & drop a CSV file"));
	});

	$upload_area.on("drop", function (e) {
		e.preventDefault();
		e.stopPropagation();
		$upload_area.removeClass("dragover");
		$drop_text.text(__("Click to upload or drag & drop a CSV file"));

		let files = e.originalEvent.dataTransfer.files;
		if (files.length) {
			upload_and_preview(files[0]);
		}
	});

	$file_input.on("change", function () {
		if ($file_input[0].files.length) {
			upload_and_preview($file_input[0].files[0]);
		}
	});

	function upload_and_preview(file) {
		$upload_area.addClass("hidden");
		$preview_section.removeClass("hidden");

		$preview_table.html(
			'<div class="text-muted text-center" style="padding: 40px;">' +
				__("Loading preview...") +
				"</div>"
		);

		new frappe.ui.FileUploader({
			dialog_title: __("Uploading"),
			doctype: "File",
			docname: "",
			files: [file],
			folder: "Home",
			on_success: function (file_doc) {
				uploaded_file_url = file_doc.file_url;
				load_preview();
			},
			on_fail: function (err) {
				frappe.msgprint(__("Upload failed: ") + err);
				reset_upload();
			},
		});
	}

	function load_preview() {
		frappe.call({
			method: "real_estate.real_estate.page.bulk_import_payments.bulk_import_payments.preview_csv",
			args: { file_url: uploaded_file_url },
			callback: function (r) {
				if (r.message) {
					render_preview(r.message);
				}
			},
			error: function () {
				frappe.msgprint(__("Failed to parse CSV. Check the format and try again."));
				reset_upload();
			},
		});
	}

	function render_preview(data) {
		let columns = data.columns.map(function (col) {
			return {
				id: col,
				name: __(frappe.model.unscrub(col)),
				content: __(frappe.model.unscrub(col)),
				editable: false,
			};
		});

		columns.push({
			id: "__booking_status",
			name: __("Booking Status"),
			content: __("Booking Status"),
			editable: false,
			width: 120,
		});

		$preview_count.text(__("{0} rows found", [data.count]));
		$preview_table.empty();

		dt_instance = new frappe.DataTable($preview_table[0], {
			columns: columns,
			data: data.rows,
			inlineFilters: true,
			cellHeight: 32,
			serialNoColumn: false,
			checkboxColumn: false,
		});

		$import_btn.removeClass("hidden");
		$import_btn.text(__("Import {0} Payment(s)", [data.count]));
	}

	$import_btn.on("click", function () {
		if (!uploaded_file_url) return;

		$import_btn.prop("disabled", true).text(__("Importing..."));

		frappe.call({
			method: "real_estate.real_estate.page.bulk_import_payments.bulk_import_payments.import_csv",
			args: { file_url: uploaded_file_url },
			callback: function (r) {
				if (r.message) {
					show_results(r.message);
				}
			},
			error: function (err) {
				frappe.msgprint(__("Import failed: ") + err);
				$import_btn.prop("disabled", false).text(__("Retry Import"));
			},
		});
	});

	function show_results(stats) {
		let html = "";
		if (stats.errors && stats.errors.length) {
			let err_list = stats.errors
				.map(function (e) {
					return "<li>" + e + "</li>";
				})
				.join("");

			html =
				'<div class="alert alert-success">' +
				__("Processed: {0}", [stats.processed]) +
				"<br>" +
				__("Skipped: {0}", [stats.skipped]) +
				"</div>" +
				'<div class="alert alert-danger"><ul>' +
				err_list +
				"</ul></div>";
		} else {
			html =
				'<div class="alert alert-success">' +
				__("All {0} payment(s) imported successfully!", [stats.processed]) +
				"</div>";
		}

		$result_content.html(html);
		$result_section.removeClass("hidden");
		$import_btn.prop("disabled", false).addClass("hidden");

		frappe.utils.scroll_to($result_section, true, 300);
	}

	function reset_upload() {
		uploaded_file_url = null;
		dt_instance = null;
		$upload_area.removeClass("hidden");
		$preview_section.addClass("hidden");
		$import_btn.addClass("hidden");
		$result_section.addClass("hidden");
		$result_content.empty();
		$file_input.val("");
	}
};
