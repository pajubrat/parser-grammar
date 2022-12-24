class SyntacticWorkingMemory:
    def __init__(self, brain_model):
        self.brain_model = brain_model
        self.working_memory = []
        self.in_active_memory = []
        self.not_in_active_memory = []

    def initialize(self):
        self.working_memory = []

    def maintain(self, site):
        if 'working_memory' in self.brain_model.local_file_system.settings and self.brain_model.local_file_system.settings['working_memory']:
            if not site.active_in_syntactic_working_memory:
                site.active_in_syntactic_working_memory = True

    def remove_item(self, ps):
        ps.active_in_syntactic_working_memory = False
        if ps.mother and (ps.contains_features({'T/fin', 'OP:REL'})):
            node = ps
            while node.mother:
                node = node.mother
                node.active_in_syntactic_working_memory = False

    def remove_items(self, merge_sites):
        for site, transfer, address_label in merge_sites:
            site.active_in_syntactic_working_memory = False

    def active_working_memory_catalog(self, ps):
        all_nodes_available = [N for N in ps.geometrical_minimal_search()]
        nodes_not_in_active_working_memory = []
        new_nodes_available = all_nodes_available.copy()
        for N in all_nodes_available:
            if not N.active_in_syntactic_working_memory:
                new_nodes_available.remove(N)
                nodes_not_in_active_working_memory.insert(0, N) # Outside list is stack
        return [node for node in new_nodes_available], [node for node in nodes_not_in_active_working_memory]
