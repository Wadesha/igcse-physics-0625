# -*- coding: utf-8 -*-
"""Generate the equations page formula.html for Cambridge IGCSE Physics 0625.

CIE IGCSE Physics does NOT give candidates a separate formula booklet, so this
page is organised the way the examination actually tests recall:
  1. the equations you must know by heart, grouped by syllabus topic;
  2. units, prefixes and conversions;
  3. the standard practical methods and safety rules.
"""
import os
from _common import BASE, CSS, MJAX_HEAD, verify_mathjax

# ---------- Data ----------
# (group, [(label, formula/text), ...])
EQUATIONS = [
    ('Motion, forces and energy', [
        ('average speed', r'v=\frac{d}{t}'),
        ('acceleration', r'a=\frac{\Delta v}{t}'),
        ('weight', r'W=mg'),
        ('density', r'\rho=\frac{m}{V}'),
        ("Hooke's law", r'F=kx'),
        ("Newton's second law", r'F=ma'),
        ('moment of a force', r'\text{moment}=F\times d'),
        ('momentum', r'p=mv'),
        ('force as rate of change of momentum', r'F=\frac{\Delta p}{t}'),
        ('kinetic energy', r'E_k=\frac{1}{2}mv^{2}'),
        ('change in gravitational potential energy', r'\Delta E_p=mg\Delta h'),
        ('work done', r'W=Fs'),
        ('power', r'P=\frac{W}{t}=\frac{E}{t}'),
        ('efficiency', r'\text{efficiency}=\frac{\text{useful output}}{\text{total input}}'),
        ('pressure', r'p=\frac{F}{A}'),
        ('pressure change in a liquid', r'\Delta p=\rho g\Delta h'),
    ]),
    ('Thermal physics', [
        ('energy and temperature rise', r'E=mc\Delta T'),
        ('specific heat capacity of water', r'c\approx 4200\ \mathrm{J/(kg\,^{\circ}C)}'),
    ]),
    ('Waves', [
        ('wave speed', r'v=f\lambda'),
        ('period and frequency', r'T=\frac{1}{f}'),
        ('refractive index', r'n=\frac{\sin i}{\sin r}'),
        ('critical angle (dense to less dense)', r'\sin c=\frac{1}{n}'),
    ]),
    ('Electricity and magnetism', [
        ('charge and current', r'Q=It'),
        ('e.m.f. and p.d.', r'E=\frac{W}{Q},\qquad V=\frac{W}{Q}'),
        ('resistance', r'R=\frac{V}{I}'),
        ("Ohm's law", r'V=IR'),
        ('electrical power', r'P=VI'),
        ('electrical energy', r'E=VIt'),
        ('resistors in series', r'R=R_1+R_2'),
        ('resistors in parallel', r'\frac{1}{R}=\frac{1}{R_1}+\frac{1}{R_2}'),
        ('potential divider', r'\frac{V_1}{V_2}=\frac{R_1}{R_2}'),
        ('transformer turns ratio', r'\frac{V_p}{V_s}=\frac{N_p}{N_s}'),
        ('transformer at 100% efficiency', r'V_p I_p=V_s I_s'),
    ]),
    ('Space physics', [
        ('average orbital speed', r'v=\frac{2\pi r}{T}'),
        ("Hubble's law", r'v=H_0 d'),
        ('one light-year', r'9.5\times 10^{15}\ \mathrm{m}'),
    ]),
]

UNITS = [
    ('Quantities and their units', [
        ('mass', 'kilogram, kg'),
        ('length', 'metre, m'),
        ('time', 'second, s'),
        ('force and weight', 'newton, N'),
        ('energy and work done', 'joule, J'),
        ('power', 'watt, W, where 1 W = 1 J/s'),
        ('pressure', 'pascal, Pa, where 1 Pa = 1 N/m squared'),
        ('electric charge', 'coulomb, C'),
        ('electric current', 'ampere, A, where 1 A = 1 C/s'),
        ('p.d. and e.m.f.', 'volt, V, where 1 V = 1 J/C'),
        ('resistance', 'ohm, the Greek letter omega'),
        ('frequency', 'hertz, Hz'),
        ('moment of a force', 'newton metre, N m'),
    ]),
    ('Prefixes', [
        ('giga, G', r'\times 10^{9}'),
        ('mega, M', r'\times 10^{6}'),
        ('kilo, k', r'\times 10^{3}'),
        ('centi, c', r'\times 10^{-2}'),
        ('milli, m', r'\times 10^{-3}'),
        ('micro', r'\times 10^{-6}'),
        ('nano, n', r'\times 10^{-9}'),
    ]),
    ('Conversions worth knowing', [
        ('density', r'1\ \mathrm{g/cm^{3}} = 1000\ \mathrm{kg/m^{3}}'),
        ('energy', r'1\ \mathrm{kW\,h} = 3.6\times 10^{6}\ \mathrm{J}'),
        ('area', r'1\ \mathrm{cm^{2}} = 10^{-4}\ \mathrm{m^{2}}'),
        ('volume', r'1\ \mathrm{cm^{3}} = 10^{-6}\ \mathrm{m^{3}}'),
        ('temperature', r'T\ \text{in kelvin} = \theta\ \text{in degrees Celsius} + 273'),
    ]),
    ('Constants you are given', [
        ('acceleration of free fall', r'g\approx 9.8\ \mathrm{m/s^{2}}\ (\text{often rounded to }10)'),
        ('speed of light in a vacuum', r'c = 3.0\times 10^{8}\ \mathrm{m/s}'),
        ('speed of sound in air', r'\approx 330\ \text{to}\ 350\ \mathrm{m/s}'),
        ('Hubble constant', r'H_0\approx 2.2\times 10^{-18}\ \mathrm{s^{-1}}'),
        ('range of human hearing', r'20\ \mathrm{Hz}\ \text{to}\ 20\,000\ \mathrm{Hz}'),
    ]),
]

TOC = [
    ('recall', '1 · Equations to know'),
    ('units', '2 · Units and conversions'),
    ('methods', '3 · Practical methods'),
]


def cell(s):
    """Wrap cells containing LaTeX markers in a display formula; otherwise plain text."""
    s = html_escape(s)
    if '\\' in s or '^' in s or '_' in s:
        return '$$%s$$' % s
    return s


def html_escape(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def table(items):
    rows = ''.join('<tr><td class="lb">%s</td><td>%s</td></tr>' % (cell(lb), cell(fx))
                   for lb, fx in items)
    return '<table class="fx"><tbody>%s</tbody></table>' % rows


def render_group(groups):
    """Accepts (group, [(label, formula/text), ...])."""
    out = []
    for gname, items in groups:
        out.append('<h3>%s</h3>' % gname)
        out.append(table(items))
    return ''.join(out)


def main():
    recall_html = render_group(EQUATIONS)
    units_html = render_group(UNITS)
    toc = ''.join('<a href="#%s">%s</a>' % (i, t) for i, t in TOC)

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambridge IGCSE Physics 0625 &middot; Equations Book</title>
{MJAX_HEAD}
<link rel="stylesheet" href="_theme.css">
<style>
table.fx{{width:100%;font-size:15px}}
table.fx td{{border:1px solid var(--line);padding:7px 10px;vertical-align:middle}}
table.fx td.lb{{width:34%;color:var(--dim);background:var(--panel2)}}
.tocbar{{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 18px}}
.tocbar a{{background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:5px 10px;font-size:13px}}
.method{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:12px 0}}
.method ol{{margin-left:18px}}
.method ul{{margin-left:18px}}
.method li{{margin:6px 0}}
</style></head>
<body>
<div class="wrap">
<div class="side">
  <h1>Cambridge IGCSE<br>Physics 0625</h1>
  <div class="sub">Equations and methods</div>
  <div class="grp">On this page</div>
  {toc}
  <div class="grp" style="margin-top:16px">Other pages</div>
  <a class="item" href="index.html">&larr; Home</a>
  <a class="item" href="slides.html">Class slides</a>
  <a class="item" href="guide.html">Study guide</a>
  <a class="item" href="practice.html">Practice</a>
</div>
<div class="main">
<div class="hero">
<h1>Equations Book</h1>
<div class="meta">
Cambridge IGCSE Physics (0625) gives candidates <b>no separate formula booklet</b> &mdash; every equation below has to be recalled and used correctly.
<b>Part 1</b> lists them by syllabus topic, <b>Part 2</b> covers units, prefixes and constants, and <b>Part 3</b> sets out the standard practical methods.
</div>
</div>

<h2 id="recall">1 &middot; Equations to know</h2>
<p class="note">These are the quantitative relationships listed in the 0625 syllabus. Learn what each symbol means as well as the equation itself &mdash; and always check that your values are in the matching SI units before substituting.</p>
{recall_html}

<h2 id="units">2 &middot; Units and conversions</h2>
<p class="note">A wrong unit is one of the easiest ways to lose marks. Convert to SI units before you calculate, and give the unit in your final answer.</p>
{units_html}

<h2 id="methods">3 &middot; Practical methods</h2>
<p class="note">These are procedures rather than single formulae &mdash; learn the steps, the apparatus and the quantities you measure.</p>

<div class="method">
<h4>Density of an irregular solid</h4>
<ol>
<li>Measure the mass of the object with a balance.</li>
<li>Part-fill a measuring cylinder with water and record the volume.</li>
<li>Lower the object in until fully submerged and record the new volume; the difference is the volume of the object.</li>
<li>Calculate the density from mass divided by volume.</li>
</ol>
<p>For a regular solid, measure its dimensions instead and calculate the volume geometrically.</p>
</div>

<div class="method">
<h4>Specific heat capacity of a metal block</h4>
<ol>
<li>Weigh the block and record its mass.</li>
<li>Place a heater in the hole in the block, with a thermometer alongside, and insulate the block.</li>
<li>Record the initial temperature, switch on for a measured time, and record the final temperature.</li>
<li>Measure the energy supplied with a joulemeter, or from the voltage, current and time.</li>
<li>Calculate the specific heat capacity from the energy, the mass and the temperature rise.</li>
</ol>
</div>

<div class="method">
<h4>Resistance of a component</h4>
<ol>
<li>Connect the component in series with an ammeter, a battery and a variable resistor.</li>
<li>Connect a voltmeter in parallel across the component.</li>
<li>Vary the variable resistor to obtain several pairs of current and p.d. readings.</li>
<li>Calculate the resistance from each pair and average the results.</li>
</ol>
</div>

<div class="method">
<h4>Speed of sound in air (echo method)</h4>
<ol>
<li>Stand a large measured distance from a tall wall or cliff.</li>
<li>Clap and start timing; stop when you hear the echo.</li>
<li>Repeat for a number of claps and divide to obtain the time for one echo.</li>
<li>Double the distance to the wall, then divide by the echo time to get the speed.</li>
</ol>
</div>

<div class="method">
<h4>Refractive index of a glass block</h4>
<ol>
<li>Place a rectangular block on paper and draw round it.</li>
<li>Shine a narrow ray into the block; mark the incident and emergent rays.</li>
<li>Remove the block and draw the ray inside it; draw the normal at the point of entry.</li>
<li>Measure the angle of incidence and the angle of refraction, and calculate their sines.</li>
<li>Calculate the refractive index as the ratio of the two sines.</li>
</ol>
</div>

<div class="method">
<h4>Half-life from a decay curve</h4>
<ol>
<li>Measure the background count rate with no source present, and subtract it from every reading.</li>
<li>Plot the corrected count rate against time.</li>
<li>Take any starting count rate and halve it; read off the time at which the curve reaches that value.</li>
<li>The difference between the two times is the half-life; repeat at another point to check.</li>
</ol>
</div>

<div class="method">
<h4>Radiation safety</h4>
<ul>
<li>Handle sources with tongs, never with bare hands, and never point a source at anyone.</li>
<li>Keep sources in a labelled, lead-lined container when not in use.</li>
<li>Minimise the time of exposure and maximise the distance from the source.</li>
<li>Use shielding: perspex for beta, lead for gamma; alpha is stopped by paper but must never be ingested.</li>
<li>Wear a film badge so that the accumulated dose is monitored.</li>
</ul>
</div>

<div class="footer">
Equations and methods follow the Cambridge IGCSE Physics (0625) syllabus for examination from 2026.
This page is an original study aid and is not affiliated with or endorsed by Cambridge University Press &amp; Assessment.
</div>
</div></div>
</body></html>"""

    out = os.path.join(BASE, 'formula.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('written', out, len(html))
    verify_mathjax(out)


if __name__ == '__main__':
    main()
