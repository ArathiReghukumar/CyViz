function scaleAttribute(data, attribute, min, max) {
    data = data.map(d => {
        d[attribute] = min + d[attribute] * (max - min);
        return d;
    });
    return data;
}

function boundNodes(nodes) {
    const constrainBox = { x: 10, y: 10, width: 1500, height: 700 };


    let minx = 99999999;
    let maxx = -99999999;
    let miny = 99999999;
    let maxy = -99999999;
    let maxsize = -9999999;
    nodes.forEach((node) => {
        if (minx > node.x) {
            minx = node.x;
        }
        if (maxx < node.x) {
            maxx = node.x;
        }
        if (miny > node.y) {
            miny = node.y;
        }
        if (maxy < node.y) {
            maxy = node.y;
        }
        if (maxsize < node.size) {
            maxsize = node.size;
        }
    });
    const scalex = (constrainBox.width - maxsize) / (maxx - minx);
    const scaley = (constrainBox.height - maxsize) / (maxy - miny);
    nodes.forEach((node) => {
        node.x = (node.x - minx) * scalex + constrainBox.x;
        node.y = (node.y - miny) * scaley + constrainBox.y;
    });
}

function preprocessData(data) {
// #data.nodes = scaleAttribute(data.nodes, 'size', 100, 1000);
    // data.edges = scaleAttribute(data.edges, 'weight', 800, 1200);
    return data;
}

function createGraph(data) {
    nodes = data.nodes;
    let fisheye = new G6.Fisheye({
        r: 60,
        showLabel: true,
        delegateStyle: {
          fill: '#f00',
          lineDash: [5, 5],
          stroke: '#666',
        },
      });
    const colors = [
        '#8FE9FF',
        '#87EAEF',
        '#FFC9E3',
        '#A7C2FF',
        '#FFA1E3',
        '#FFE269',
        '#BFCFEE',
        '#FFA0C5',
        '#D5FF86',
      ];
    graph = new G6.Graph({
        container: 'container',
        width,
        height,
        modes: {
            default: ['drag-canvas', 'zoom-canvas', 'activate-relations', 'drag-node']
        },
        plugins: [fisheye],
        animate: true,
        animateCfg: {
            duration: 500, // Number, the duration of one animation
            // easing: 'easePolyIn', // String, the easing function
        },

        defaultNode:{size: 30},

        layout: {
            type: 'circular',
            center: [700, 400], // The center of the graph by default
            radius: null,
            startRadius: 150,
            endRadius: 450,
            clockwise: false,
            // divisions: 5,
            ordering: 'topology',
            angleRatio: 1.6,
            workerEnabled: true,
            fitView: true
    },
});

    graph.data({
        nodes: nodes,
        edges: data.edges.map(function (edge, i) {
            edge.id = 'edge' + i;
            return Object.assign({}, edge);
        }),
    });

    graph.render();
    graph.getNodes().forEach((node) => {
        node
          .getContainer()
          .getChildren()
          .forEach((shape) => {
            if (shape.get('type') === 'text') shape.hide();
           });
      });

    if (typeof window !== 'undefined')
        window.onresize = () => {
            if (!graph || graph.get('destroyed')) return;
            if (!container || !container.scrollWidth || !container.scrollHeight) return;
            graph.changeSize(container.scrollWidth, container.scrollHeight);
        };
}