window.addEventListener('load', function () {
    function toggle(event) {
        let rowId = 'details-' + event.target.getAttribute('office-name');
        let detailsRow = document.getElementById(rowId);

        if (!detailsRow) {
            return;
        }

        if (detailsRow.style.display === 'none') {
            detailsRow.style.display = 'table-row';
            event.target.innerHTML = 'Ukryj szczegóły';
        } else {
            event.target.innerHTML = 'Pokaż szczegóły';
            detailsRow.style.display = 'none';
        }

    }
    document.querySelectorAll('.show-office-details').forEach((btn) => btn.addEventListener('click', toggle));
    // Validation Logic
    (function () {
        'use strict'
        var forms = document.querySelectorAll('.needs-validation')
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    }

                    // Restart animation if already validated
                    if (form.classList.contains('was-validated')) {
                        form.classList.remove('was-validated');
                        void form.offsetWidth; // Trigger reflow
                    }
                    form.classList.add('was-validated')
                }, false)
            })
    })()
});
