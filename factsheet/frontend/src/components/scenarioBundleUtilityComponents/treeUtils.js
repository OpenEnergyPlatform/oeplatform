// Helper to find all parents of selected nodes
export const getCheckedWithParents = (checkedIds, allNodes) => {
  const parentMap = new Map();

  // 1. Build a map of child -> parent
  const buildParentMap = (nodes, parentId = null) => {
    // Safety check: ensure nodes is an array
    if (!Array.isArray(nodes)) return;

    nodes.forEach((node) => {
      if (parentId) parentMap.set(node.value, parentId);
      if (node.children) buildParentMap(node.children, node.value);
    });
  };
  
  // Ensure we are working with an array
  const safeNodes = Array.isArray(allNodes) ? allNodes : [allNodes];
  buildParentMap(safeNodes);

  // 2. For every checked ID, walk up the tree and add ancestors
  const newChecked = new Set(checkedIds);
  checkedIds.forEach((id) => {
    let currentId = id;
    while (parentMap.has(currentId)) {
      const parent = parentMap.get(currentId);
      newChecked.add(parent);
      currentId = parent;
    }
  });

  return Array.from(newChecked);
};


// Helper: recursively filter the tree to keep only selected nodes and their ancestors
export const filterTree = (nodes, selectedValues) => {
  // Ensure we have an array to work with
  const safeNodes = Array.isArray(nodes) ? nodes : [];
  
  const selectedSet = new Set(selectedValues);

  const filterNode = (node) => {
    let filteredChildren = [];
    if (node.children && Array.isArray(node.children)) {
      filteredChildren = node.children
        .map(filterNode)
        .filter((child) => child !== null);
    }

    // Keep node if it's in the selection OR if it has children that are kept
    // We compare node.value (the ID) with the selected values
    if (selectedSet.has(node.value) || filteredChildren.length > 0) {
      return {
        ...node,
        children: filteredChildren.length > 0 ? filteredChildren : undefined,
      };
    }
    return null;
  };

  return safeNodes.map(filterNode).filter((node) => node !== null);
};