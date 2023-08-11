$(document).ready(function() {
    $("#search-form").submit(function(event) {
        event.preventDefault(); // Prevent default form submission

        var formData = $(this).serialize(); // Serialize form data
        $.ajax({
            type: "POST",
            url: "/search", // Flask route for search
            data: formData,
            success: function(response) {
                $("#search-results").html(response); // Update results on the page
            }
        });
    });
});
