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
    data.nodes = scaleAttribute(data.nodes, 'size', 10, 100);
    data.edges = scaleAttribute(data.edges, 'weight', 800, 1200);
    return data;
}

function createGraph(data) {
    nodes = data.nodes;
    graph = new G6.Graph({
        container: 'container',
        width,
        height,
        modes: {
            default: ['drag-canvas', 'zoom-canvas', 'activate-relations', 'drag-node']
        },
        animate: true,
        animateCfg: {
            duration: 500, // Number, the duration of one animation
            // easing: 'easePolyIn', // String, the easing function
        },

        layout: {
            type: 'gForce',
            center: [800, 500],
            edgeStrength: (e) => { return e.weight; },
            nodeStrength: (n) => { return n.size; },
            linkDistance: 400,
            gravity: 50,
            damping: 0.5,
            preventOverlap: true,
            nodeSize: (n) => { return 200 + n.size; },
            workerEnabled: true, // Whether to activate web-worker
            // gpuEnabled: true,
            // onTick
        }
    });

    graph.data({
        nodes: nodes,
        edges: data.edges.map(function (edge, i) {
            edge.id = 'edge' + i;
            return Object.assign({}, edge);
        }),
    });

    graph.render();

    if (typeof window !== 'undefined')
        window.onresize = () => {
            if (!graph || graph.get('destroyed')) return;
            if (!container || !container.scrollWidth || !container.scrollHeight) return;
            graph.changeSize(container.scrollWidth, container.scrollHeight);
        };
}

function nextFrame() {
    return fetch('http://127.0.0.1:5000/data/' + (currFrameNumber + 1))
        .then((res) => res.json())
        .then((data) => preprocessData(data))
        .then((data) => {graph.changeData(data);})
        .then(() => currFrameNumber = currFrameNumber + 1) 
}

function prevFrame() {
    return fetch('http://127.0.0.1:5000/data/' + (currFrameNumber - 1))
        .then((res) => res.json())
        .then((data) => preprocessData(data))
        .then((data) => {graph.changeData(data);})
        .then(() => currFrameNumber = currFrameNumber - 1) 
}


