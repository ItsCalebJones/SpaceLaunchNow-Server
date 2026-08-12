/*
 * launch-time.js
 *
 * Upgrades server-rendered <time class="sln-time"> elements from UTC to the
 * viewer's local timezone, keeping the UTC value visible beneath it.
 *
 * The server has already decided whether a given NET is precise enough to
 * carry a time of day (see launch_time_context in web/templatetags/sln_utils.py).
 * Elements without a data-time-parts attribute are coarse -- "Q3 2026",
 * "During the 2020s" -- and are left exactly as rendered. This file contains
 * no precision logic of its own.
 */
(function () {
    "use strict";

    // Intl options per time granularity. Mirrors _UTC_TIME_FMT server-side.
    var TIME_PARTS = {
        hms: {hour: "numeric", minute: "2-digit", second: "2-digit"},
        hm: {hour: "numeric", minute: "2-digit"},
        h: {hour: "numeric"}
    };

    function localise(el) {
        var parts = TIME_PARTS[el.getAttribute("data-time-parts")];
        if (!parts) {
            return; // coarse precision: leave the server's text alone
        }

        var date = new Date(el.getAttribute("datetime"));
        if (isNaN(date.getTime())) {
            return; // unparseable: the UTC fallback is still correct
        }

        var options = {year: "numeric", month: "long", day: "2-digit", timeZoneName: "short"};
        for (var key in parts) {
            if (Object.prototype.hasOwnProperty.call(parts, key)) {
                options[key] = parts[key];
            }
        }

        var formatted;
        try {
            formatted = new Intl.DateTimeFormat(undefined, options).format(date);
        } catch (err) {
            return; // no Intl support: the UTC fallback stands
        }

        var prefix = el.getAttribute("data-prefix");
        if (prefix) {
            formatted = prefix + " " + formatted;
        }

        var local = document.createElement("span");
        local.className = "sln-time-local";
        local.textContent = formatted;

        el.insertBefore(local, el.firstChild);

        var base = el.querySelector(".sln-time-base");
        if (base) {
            base.classList.add("sln-time-secondary");
        }
    }

    function run() {
        var nodes = document.querySelectorAll("time.sln-time");
        for (var i = 0; i < nodes.length; i++) {
            localise(nodes[i]);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", run);
    } else {
        run();
    }
})();
