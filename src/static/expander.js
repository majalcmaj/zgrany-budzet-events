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
});
