/* Click-to-play video facade.
 *
 * One delegated listener for the whole page, so facades rendered inside
 * lazily-loaded fragments work without re-binding. Replaces the facade's contents
 * with the real YouTube iframe on activation; autoplay is safe here because the
 * swap is always user-initiated.
 */
(function () {
    "use strict";

    document.addEventListener("click", function (event) {
        if (!event.target || !event.target.closest) {
            return;
        }
        var button = event.target.closest(".sln-video-play");
        if (!button) {
            return;
        }
        var wrapper = button.closest(".sln-video-facade");
        if (!wrapper) {
            return;
        }
        var code = wrapper.getAttribute("data-video-code");
        if (!code) {
            return;
        }

        var iframe = document.createElement("iframe");
        iframe.src =
            "https://www.youtube.com/embed/" + encodeURIComponent(code) + "?autoplay=1";
        iframe.title = wrapper.getAttribute("data-video-title") || "Video player";
        iframe.setAttribute(
            "allow",
            "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
        );
        iframe.setAttribute("allowfullscreen", "");
        iframe.setAttribute("frameborder", "0");

        wrapper.innerHTML = "";
        wrapper.appendChild(iframe);
    });
}());
