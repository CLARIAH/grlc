function log() {
  if ('console' in window) {
    console.log.apply(console, arguments);
  }
}

/**
 * Set the links `< Prev` and `Next >` href targets to next and previous commit
 * respectively.
 */
function set_commit_links(api) {
  let base = api['basePath'];
  if(base.includes('commit')) {
    base = base.split('commit')[0];
  }
  if (api['prev_commit']) {
    const prev_target = base + 'commit/' + api['prev_commit'];
    $('#prev-commit').attr('onclick', 'redirectTo(" ' + prev_target + '")');
    $('#prev-commit').show();
  } else {
    $('#prev-commit').hide();
  }
  if (api['next_commit']) {
    const next_target = base + 'commit/' + api['next_commit'];
    $('#next-commit').attr('onclick', 'redirectTo(" ' + next_target + '")');
    $('#next-commit').show();
  } else {
    $('#next-commit').hide();
  }
}

function redirectTo(url) {
  location.href= url;
}

/**
 * Set's `Oh yeah ?` link action so it displays provenance when clicked.
 */
function get_prov(api) {
  $('#ohyeahdiv').show();
  data = api['prov'].split("\n");
  var html = '<button class="btn" data-clipboard-target="#provdump">Copy</button><br><br><div id="provdump">';
  for (var i=0; i < data.length; i++) {
    html += '<div class="swagger-ui-wrap">' + data[i].replace("<", "&lt;").replace(">", "&gt;") + '</div>';
  }
  html += '</div>';
  $('#prov').html(html).linkify({target: "_blank"}).hide();
}

/**
 * This function gets called when SwaggerUIBundle finishes loading.
 */
function grlcOnComplete() {
  if(typeof ui.initOAuth == "function") {
    ui.initOAuth({
      clientId: "your-client-id",
      clientSecret: "your-client-secret-if-required",
      realm: "your-realms",
      appName: "your-app-name",
      scopeSeparator: ","
    });
  }
  // Extract JSON representation of spec
  const spec = ui.spec();
  const swaggerApi = JSON.parse(spec.toObject()['spec'])
  get_prov(swaggerApi);
  set_commit_links(swaggerApi);

  if(window.SwaggerTranslator) {
    window.SwaggerTranslator.translate();
  }

  $('pre code').each(function(i, e) {
    hljs.highlightBlock(e)
  });
}

function grlcOnFailure(data) {
  log("Unable to Load SwaggerUI");
}

/**
 * Toggle visualize provenance
 */
function grlcProvToggle(e){
  var prov = $('#prov');
  if (prov.is(":visible")) {
    prov.hide();
  } else {
    prov.show();
  }
}

/**
 * Called when window is fully loaded. It then triggers creation of SwaggerUIBundle.
 *
 */
function grlcOnLoad(url) {
  // Build a system
  const ui = SwaggerUIBundle({
    url: url,
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl,
      GrlcLayoutPlugin
    ],
    layout: "GrlcLayout",
    validatorUrl: undefined, // required ??
    supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
    onComplete: grlcOnComplete,
    onFailure: grlcOnFailure,
    docExpansion: "list",
    apisSorter: "alpha",
    showRequestHeaders: true
  });
  window.ui = ui;
}
