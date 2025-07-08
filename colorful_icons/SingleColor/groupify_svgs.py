import os
import xml.etree.ElementTree as ET

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace('', SVG_NAMESPACE)

def groupify_svg(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Find the first <g> (if any)
    g_main = None
    for g in root.findall(f'.//{{{SVG_NAMESPACE}}}g'):
        if g.get('id') == 'main':
            g_main = g
            break
    if g_main is not None:
        return False  # Already grouped

    # Find all top-level shapes
    shapes = []
    for tag in ['path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline']:
        shapes.extend(root.findall(f'.//{{{SVG_NAMESPACE}}}{tag}'))
    if not shapes:
        return False  # Nothing to group

    # Create new <g id="main">
    g = ET.Element(f'{{{SVG_NAMESPACE}}}g', {'id': 'main'})
    for shape in shapes:
        parent = shape.getparent() if hasattr(shape, 'getparent') else None
        if parent is not None:
            parent.remove(shape)
        g.append(shape)
    root.append(g)
    tree.write(svg_path, encoding='utf-8', xml_declaration=True)
    return True

def main():
    processed = 0
    skipped = 0
    for fname in os.listdir('.'):
        if fname.lower().endswith('.svg'):
            try:
                changed = groupify_svg(fname)
                if changed:
                    print(f'Grouped: {fname}')
                    processed += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'Error processing {fname}: {e}')
    print(f'Processed: {processed}, Skipped: {skipped}')

if __name__ == '__main__':
    main() 