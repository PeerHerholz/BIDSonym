"""
Interfaces to generate reportlets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

SUBJECT_TEMPLATE = """\
\t<ul class="elem-desc">
\t\t<li>Subject ID: {subject_id}</li>
\t\t<li>Structural images: {n_t1s:d} T1-weighted {t2w}</li>
\t\t<li>Meta data fields deleted: {meta_fields} </li>
\t\t<li>defacing algorithm used: {defacing_algorithm} {version_defacing}</li>
\t</ul>
"""

ABOUT_TEMPLATE = """\t<ul>
\t\t<li>BIDSonym version: {version}</li>
\t\t<li>BIDSonym command: <code>{command}</code></li>
\t\t<li>Date preprocessed: {date}</li>
\t</ul>
</div>
"""
