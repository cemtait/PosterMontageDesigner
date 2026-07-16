from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout, QWidget

from poster_montage_designer.version import APP_VERSION


GUIDE_HTML = r"""
<!doctype html>
<html>
<head>
<style>
body { color: #dddddd; background: #252525; font-family: 'Segoe UI'; font-size: 10.5pt; line-height: 1.42; }
h1 { color: #ffffff; font-size: 24pt; margin: 0 0 4px 0; }
h2 { color: #8dc8ff; font-size: 15pt; margin-top: 26px; border-bottom: 1px solid #484848; padding-bottom: 5px; }
h3 { color: #f0f0f0; font-size: 11.5pt; margin-top: 18px; }
p, li { margin-top: 5px; margin-bottom: 5px; }
ul, ol { margin-top: 6px; }
code { background: #181818; color: #d9ecff; padding: 2px 5px; }
.note { background: #202a31; border-left: 4px solid #5e9ccc; padding: 10px 12px; margin: 12px 0; }
.tip { background: #292920; border-left: 4px solid #b5a659; padding: 10px 12px; margin: 12px 0; }
a { color: #73bdf2; }
.small { color: #aaaaaa; font-size: 9pt; }
</style>
</head>
<body>
<h1>Posterfolio User Guide</h1>
<p class="small">Version __VERSION__</p>
<p>Posterfolio creates high-quality poster montages from an IMDb filmography. Import your credits, choose the poster artwork you prefer, refine the arrangement, and export a print-ready image or PDF.</p>

<h2>Quick Start</h2>
<ol>
<li>Add your free TMDb API Read Access Token in <b>Edit → Settings…</b>.</li>
<li>Choose <b>File → Import from IMDb…</b>, open an IMDb person page, and press <b>Import Credits</b>.</li>
<li>Choose posters, shuffle or arrange the layout, adjust the canvas and Airiness, then choose <b>File → Export…</b>.</li>
</ol>

<h2>Setting up TMDb</h2>
<p>Posterfolio identifies credits from IMDb, but obtains poster artwork and supporting title information from <b>The Movie Database (TMDb)</b>. A free TMDb account and API Read Access Token are required.</p>
<ol>
<li>Open <a href="https://www.themoviedb.org/signup">themoviedb.org/signup</a> and create a free account.</li>
<li>After signing in, open your TMDb account settings and select <b>API</b>.</li>
<li>Request an API key. For normal personal use, choose the developer option and complete the short application form.</li>
<li>On the API page, copy the long <b>API Read Access Token</b> (the token beginning with a JWT-style string), rather than the shorter v3 API key.</li>
<li>In Posterfolio, choose <b>Edit → Settings…</b>, paste the token into the TMDb token field, and save.</li>
</ol>
<div class="note"><b>Privacy:</b> Posterfolio stores the token locally in its settings file. It is used only to make requests to TMDb.</div>

<h2>Importing IMDb credits</h2>
<p>Choose <b>File → Import from IMDb…</b> or press <b>Import from IMDb…</b> in the Project panel. Posterfolio opens an embedded web browser at IMDb.</p>
<ol>
<li>Navigate to the required IMDb person page.</li>
<li>Allow the filmography to load. Scroll through it if IMDb has not yet expanded all credits.</li>
<li>Press <b>Import Credits</b>.</li>
</ol>
<p>Posterfolio creates a new project, obtains the available posters from TMDb, chooses a strong initial poster for each title, and builds the montage.</p>
<div class="tip">The initial poster is usually a good choice because Posterfolio prefers English-language artwork and presents posters with the highest TMDb community vote counts first.</div>

<h2>The Project panel</h2>
<h3>Import from IMDb…</h3>
<p>Starts a new project from an IMDb person page. Importing replaces the current project, so save anything you wish to keep first.</p>

<h3>Arrange By</h3>
<p>Reorders the active posters using one of the available metadata-based arrangements:</p>
<ul>
<li><b>Chronological</b> — newest titles first.</li>
<li><b>Popularity</b> — highest TMDb popularity first.</li>
<li><b>Box Office</b> — highest recorded revenue first where data is available.</li>
</ul>

<h3>Shuffle</h3>
<p>Randomises the poster order. Press it repeatedly to explore alternative compositions. Shuffle changes the order, while the layout engine still decides the best grid for the chosen canvas.</p>

<h3>Project summary</h3>
<ul>
<li><b>Imported</b> — all titles currently in the project.</li>
<li><b>Visible</b> — posters currently placed on the canvas.</li>
<li><b>Benched</b> — titles held outside the current montage.</li>
<li><b>Missing</b> — titles for which Posterfolio could not obtain usable poster artwork.</li>
</ul>

<h2>Choosing poster artwork</h2>
<p>Click a poster on the canvas to select it. The selected poster appears in the Project panel.</p>
<p>Use the left and right arrow buttons beneath the preview to browse its available poster variants. The counter shows, for example, <code>Poster 4 of 12</code>. If there is only one usable poster, the arrows are disabled and the label simply reads <code>Poster</code>.</p>
<p>Posterfolio prefers English posters. If a title has no English-tagged artwork, it falls back gracefully so the title is not left without a poster.</p>

<h2>The Bench</h2>
<p>The Bench is a holding area, not a recycle bin. A benched title remains part of the project but does not currently occupy a cell on the canvas.</p>
<ul>
<li>Drag a poster from the canvas into the Bench to remove it from the montage without deleting it.</li>
<li>Drag a poster from the Bench onto a canvas poster to replace that poster. The displaced poster moves to the Bench.</li>
<li>Right-click a benched poster for actions such as <b>Promote</b>, <b>Open on IMDb</b>, or <b>Delete from Project</b>.</li>
</ul>
<p>The layout engine may also bench titles automatically when the selected canvas shape cannot accommodate every poster attractively. Changing the canvas or Airiness can allow automatically benched titles to return.</p>
<div class="note"><b>Bench versus Delete:</b> Bench means “not in this layout for now.” Delete permanently removes the title from the project, although it can still be undone with Ctrl+Z until the project is closed.</div>

<h2>Automatic poster layout</h2>
<p>Posterfolio calculates how the posters can best fit the selected canvas. It chooses the number of rows and columns, poster dimensions, and spacing while preserving poster proportions and making effective use of the available area.</p>
<p>The layout is therefore responsive rather than fixed. It will be recalculated when you:</p>
<ul>
<li>change the canvas preset;</li>
<li>enter a custom width or height;</li>
<li>change the canvas aspect ratio;</li>
<li>change Airiness;</li>
<li>bench, promote, delete, or add titles;</li>
<li>shuffle or choose an Arrange By option.</li>
</ul>
<p>A landscape canvas, a portrait canvas, and a square canvas can produce very different arrangements from the same collection of posters. This is expected: Posterfolio is continually seeking the best fit for the current canvas.</p>

<h2>Canvas size and printing</h2>
<p>The Canvas menu provides common presets, including standard poster sizes and screen aspect ratios. Width and Height can also be entered manually in millimetres by choosing or creating a custom size.</p>
<div class="tip"><b>Useful printing workflow:</b> Check the standard sizes offered by the print shop you intend to use. Choose the size you plan to order, enter those dimensions into Posterfolio, and refine the montage while viewing the exact intended aspect ratio.</div>
<p>Changing the physical dimensions while retaining the same aspect ratio may not greatly alter the on-screen arrangement, but it determines the physical size represented by the project and influences export calculations.</p>

<h2>Airiness</h2>
<p>Airiness controls how much breathing room surrounds and separates posters.</p>
<ul>
<li><b>Lower Airiness</b> produces larger posters and a tighter, denser montage.</li>
<li><b>Higher Airiness</b> increases spacing and creates a more open composition.</li>
</ul>
<p>A good workflow is to decide the canvas size and aspect ratio first, then adjust Airiness. Because spacing affects how many posters can fit, changing Airiness may alter the grid or move some posters to or from the Bench.</p>

<h2>Canvas Colour</h2>
<p>Press <b>Canvas Colour…</b> to choose the background visible between and around posters. The colour is stored in the project and included in exported artwork.</p>

<h2>Dragging posters</h2>
<ul>
<li>Drag one canvas poster onto another to swap their positions.</li>
<li>The dragged poster remains the size it occupies in the layout, becomes slightly translucent, and leaves a placeholder behind.</li>
<li>Drag from the canvas to the Bench to bench a title.</li>
<li>Drag from the Bench onto the canvas to replace a visible title.</li>
</ul>

<h2>File menu</h2>
<ul>
<li><b>New Project</b> — clears the current work and creates an empty project.</li>
<li><b>Open Project…</b> — opens a Posterfolio <code>.pmd</code> file.</li>
<li><b>Save Project</b> — saves to the current project file.</li>
<li><b>Save Project As…</b> — saves a new copy or chooses a new location.</li>
<li><b>Import from IMDb…</b> — starts a new project from an IMDb person page.</li>
<li><b>Export…</b> — opens the export settings and writes the completed artwork.</li>
<li><b>Exit</b> — closes Posterfolio.</li>
</ul>

<h2>Edit menu</h2>
<ul>
<li><b>Undo / Redo</b> — reverses or reapplies recent project changes.</li>
<li><b>Settings…</b> — stores the TMDb API Read Access Token and application preferences.</li>
</ul>

<h2>Project files and poster cache</h2>
<p>Posterfolio projects use the <code>.pmd</code> extension. A project records its imported titles, poster choices, Bench state, order, canvas dimensions, Airiness, and canvas colour.</p>
<p>The poster image files are cached separately on the computer. This keeps project files small and allows previously downloaded artwork to load quickly. Opening a project reconnects its title and poster choices to the local cache and downloads anything that is missing.</p>

<h2>Exporting and render quality</h2>
<p>Choose <b>File → Export…</b>. The export dialog offers PNG, JPEG, TIFF, and PDF output.</p>
<p>The preview and montage canvas use responsive display images for speed. During export, Posterfolio uses the full-size cached source poster images rather than enlarging the small thumbnails visible in the interface.</p>
<p>The export-size slider runs up to the calculated maximum size at which the source posters should not need to be enlarged beyond their available pixels. Moving it left creates a smaller image. The resulting pixel dimensions are shown directly in the dialog.</p>
<ul>
<li><b>PNG</b> — lossless and widely supported; useful for high-quality digital output.</li>
<li><b>JPEG</b> — smaller files; useful for sharing or print services accepting JPEG.</li>
<li><b>TIFF</b> — large, high-quality image files for suitable professional workflows.</li>
<li><b>PDF</b> — convenient for print delivery and document-oriented workflows.</li>
</ul>

<h3>Where exported files go</h3>
<p>After choosing the export settings, Posterfolio opens a standard Save dialog. The rendered file is written to the folder and filename you select. Posterfolio remembers the last export folder for the next export.</p>
<p>The exported image or PDF is separate from the <code>.pmd</code> project. Saving the project does not render an image, and exporting does not replace the project file.</p>

<h2>Practical tips</h2>
<ul>
<li>Choose the intended print dimensions before spending too long refining the layout.</li>
<li>Try several Shuffle results; Ctrl+Z can return to a previous order.</li>
<li>Use the Bench rather than deleting titles while experimenting.</li>
<li>Adjust Airiness after choosing the canvas shape.</li>
<li>For printing, export at the largest practical setting accepted by your print provider.</li>
<li>Save the <code>.pmd</code> project before major experiments so it can be revisited later.</li>
</ul>

<h2>Credits and services</h2>
<p>Posterfolio __VERSION__</p>
<p>Designed and written by <b>Charles Tait</b>.<br>
Built with Python and Qt.<br>
Poster images and supporting metadata provided by TMDb.</p>
<p class="small">Posterfolio is not affiliated with IMDb or TMDb. IMDb is used to identify filmography titles; artwork and supporting metadata are requested from TMDb.</p>
</body>
</html>
""".replace("__VERSION__", APP_VERSION)


class UserGuideDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Posterfolio User Guide")
        self.resize(820, 760)
        self.setMinimumSize(640, 520)

        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        self.browser.setHtml(GUIDE_HTML)
        self.browser.anchorClicked.connect(self._open_external_link)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.browser, 1)
        layout.addWidget(buttons)

    def _open_external_link(self, url: QUrl) -> None:
        QDesktopServices.openUrl(url)
