<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{% block title %}My Website{% endblock %}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <!-- Shared Styles -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.1/css/all.min.css">

  <!-- Core API URLs (✅ Must load FIRST) -->
  <script src="{{ url_for('static', filename='js/api_routes.js') }}"></script>

  <!-- Core Base Functions (✅ Must load SECOND) -->
  <script src="{{ url_for('static', filename='js/base.js') }}"></script>

  <!-- Theme Stylesheet Decider -->
  <link id="themeStylesheet" rel="stylesheet" href="">

  {% block extra_styles %}{% endblock %}

  <!-- Preload Critical Images -->
  <link rel="preload" href="{{ url_for('static', filename='images/btc_logo.png') }}" as="image">
  <link rel="preload" href="{{ url_for('static', filename='images/eth_logo.png') }}" as="image">
  <link rel="preload" href="{{ url_for('static', filename='images/sol_logo.png') }}" as="image">
  <link rel="preload" href="{{ url_for('static', filename='images/obivault.jpg') }}" as="image">
  <link rel="preload" href="{{ url_for('static', filename='images/r2vault.jpg') }}" as="image">

  <!-- Theme Setup Early -->
  <script>
    (function() {
      const themeMode = localStorage.getItem('themeMode') || 'light';
      document.documentElement.classList.add(themeMode + '-bg');
      const themeLink = document.getElementById('themeStylesheet');
      if (themeMode === 'dark') {
        themeLink.href = "{{ url_for('static', filename='css/base_dark.css') }}";
      } else {
        themeLink.href = "{{ url_for('static', filename='css/base_light.css') }}";
      }
    })();
  </script>

  <!-- Root Variables for Backgrounds -->
  <style>
    :root {
      --light-page-bg-color: #f5f5f5;
      --light-page-text-color: #000;
      --dark-page-bg-color: #3a3838;
      --dark-page-text-color: #ddd;
    }
    body.light-bg {
      background-color: var(--light-page-bg-color) !important;
      color: var(--light-page-text-color) !important;
      background-image: none !important;
    }
    body.dark-bg {
      background-color: var(--dark-page-bg-color) !important;
      color: var(--dark-page-text-color) !important;
      background-image: none !important;
    }
  </style>
</head>

<body class="hold-transition layout-top-nav">
  <div class="wrapper">
    {% include "title_bar.html" %}

    <!-- Main Content -->
    <div class="content-wrapper">
      <div class="content">
        <div id="layoutContainer" class="container-fluid">
          {% block page_title %}{% endblock %}
          <div class="pt-5">
            {% block content %}{% endblock %}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Shared Libraries -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.4/jquery.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>

  {% block extra_scripts %}{% endblock %}

  <!-- Layout & Dynamic Theme Finalizer -->
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      const layoutMode = localStorage.getItem("layoutMode") || "fluid";
      const allLayouts = document.querySelectorAll('.container, .container-fluid');
      allLayouts.forEach(wrapper => {
        wrapper.classList.remove('container', 'container-fluid');
        wrapper.classList.add(layoutMode === "fixed" ? "container" : "container-fluid");
      });

      const themeToggleButton = document.getElementById('themeToggleButton');
      if (themeToggleButton) {
        themeToggleButton.addEventListener('click', function() {
          const themeIcon = document.getElementById('themeIcon');
          const themeLink = document.getElementById('themeStylesheet');
          const currentMode = localStorage.getItem('themeMode') || 'light';
          const newMode = (currentMode === 'light') ? 'dark' : 'light';

          document.body.classList.remove('light-bg', 'dark-bg');
          document.body.classList.add(newMode + '-bg');
          document.body.style.transition = 'background-color 0.4s ease, color 0.4s ease';

          if (newMode === 'dark') {
            themeLink.href = "{{ url_for('static', filename='css/base_dark.css') }}";
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
          } else {
            themeLink.href = "{{ url_for('static', filename='css/base_light.css') }}";
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
          }

          localStorage.setItem('themeMode', newMode);
        });
      }
    });
  </script>

</body>
</html>
