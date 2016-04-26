# -*- coding: utf-8 -*-
xhtmlInput = '''
<!-- "margin-left" property on paragraphs -->
<p>Normal paragraph with a specia char\n\t\v\x0cUn montant de \x0b\v145,00 \xe2\x82\xac TVAC</p>
<p style="margin-left: 25px">25px margin left</p>
<p style="margin-left: 4cm">4cm margin left</p>
<p style="margin-left:-1cm">Text with a negative left margin</p>

<!-- Text alignment within table cells (ckeditor-generated) -->
<table border="1" cellpadding="1" cellspacing="1" style="width:500px">
 <tbody>
  <tr>
   <td>Left-aligned text</td>
   <td style="text-align: center;">Centered text</td>
  </tr>
  <tr>
   <td style="text-align: right;">Right-aligned text</td>
   <td></td>
  </tr>
 </tbody>
</table>

<!-- Text alignment within paragraphs and divs -->
<p style="text-align: left">Left-aligned text</p>
<p style="text-align: right; margin-right: 30px">Right-aligned + margin rigth</p>
<p style="text-align: justify; margin-left: 2cm; margin-right: 2cm">Justified ext between margins Justified ext between margins
Justified ext between margins Justified ext between margins Justified ext between margins Justified ext between margins Justified ext between margins
justified ext between margins Justified ext between margins Justified ext between margins Justified ext between margins</p>
<div style="text-align: center; margin-top: 30px">Margin top + center in a div</div>
<p style="margin-left: 4cm">Second with 4cm margin left, to check if a single style will be generated</p>
'''
