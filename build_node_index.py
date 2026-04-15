#!/usr/bin/env python3
"""
Build a lightweight node index that maps each node to its segment.
This allows instant lookups without loading the full 28MB JSON.
"""

import json
from pathlib import Path
from collections import defaultdict

# Segment files with their metadata
SEGMENTS = {
    'people': 'chabadpedia_knowledge_graph_people.json',
    'places': 'chabadpedia_knowledge_graph_places.json',
    'concepts': 'chabadpedia_knowledge_graph_concepts.json',
    'publications': 'chabadpedia_knowledge_graph_publications.json',
    'organizations': 'chabadpedia_knowledge_graph_organizations.json',
    'rebbes': 'chabadpedia_knowledge_graph_rebbes.json',
}

def load_segment_nodes(filepath):
    """Load just the nodes from a segment file."""
    print(f"  Loading {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        nodes_array = []
        nodes = data.get('nodes', {})

        if isinstance(nodes, list):
            nodes_array = nodes
        else:
            for key in nodes:
                nodes_array.append(nodes[key])

        return nodes_array
    except FileNotFoundError:
        print(f"    Segment not found: {filepath}")
        return []

def build_node_to_segment_map():
    """Build a map of node title -> segments it appears in."""
    node_segments = defaultdict(list)
    node_data = {}

    for segment_name, filename in SEGMENTS.items():
        print(f"\nProcessing segment: {segment_name}")
        nodes = load_segment_nodes(filename)

        for node in nodes:
            title = node.get('title')
            if title:
                if segment_name not in node_segments[title]:
                    node_segments[title].append(segment_name)

                # Store node metadata for quick lookup
                if title not in node_data:
                    node_data[title] = {
                        'title': title,
                        'categories': node.get('categories', []),
                        'links_count': node.get('links_count', 0),
                        'is_redirect': node.get('is_redirect', False),
                        'segments': []
                    }
                node_data[title]['segments'].append(segment_name)

    return node_data, node_segments

def build_category_index(node_data):
    """Build category -> nodes mapping."""
    category_nodes = defaultdict(list)

    for title, data in node_data.items():
        for category in data.get('categories', []):
            category_nodes[category].append({
                'title': title,
                'links_count': data.get('links_count', 0)
            })

    # Sort each category's nodes by connection count
    for category in category_nodes:
        category_nodes[category].sort(key=lambda x: x['links_count'], reverse=True)

    return dict(category_nodes)

def main():
    print("=" * 60)
    print("Building Node Index for ChabadPedia Knowledge Graph")
    print("=" * 60)

    # Build node to segment map
    node_data, node_segments = build_node_to_segment_map()

    print(f"\n✓ Found {len(node_data)} unique nodes across segments")

    # Build category index
    print("\nBuilding category index...")
    category_index = build_category_index(node_data)
    print(f"✓ Found {len(category_index)} categories")

    # Create the index file
    index = {
        'version': 1,
        'generated': '2026-04-14',
        'stats': {
            'total_nodes': len(node_data),
            'total_categories': len(category_index),
            'segments': list(SEGMENTS.keys())
        },
        'nodes': node_data,
        'categories': category_index
    }

    # Write index
    output_file = 'chabadpedia_node_index.json'
    print(f"\nWriting index to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    file_size = Path(output_file).stat().st_size
    size_mb = file_size / (1024 * 1024)

    print(f"\n{'=' * 60}")
    print(f"✓ Index built successfully!")
    print(f"  File: {output_file}")
    print(f"  Size: {size_mb:.2f} MB ({file_size:,} bytes)")
    print(f"  Nodes: {len(node_data):,}")
    print(f"  Categories: {len(category_index):,}")
    print(f"{'=' * 60}\n")

    # Show some sample data
    print("Sample nodes:")
    sample_titles = list(node_data.keys())[:5]
    for title in sample_titles:
        data = node_data[title]
        print(f"  • {title} ({data['links_count']} connections) in: {', '.join(data['segments'])}")

    print("\nTop 5 categories by node count:")
    sorted_cats = sorted(category_index.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for category, nodes in sorted_cats:
        print(f"  • {category}: {len(nodes):,} nodes")

if __name__ == '__main__':
    main()
