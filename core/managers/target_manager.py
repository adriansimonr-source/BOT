class TargetManager:


    def select_target(
        self,
        targets,
        rules
    ):


        valid_targets = []


        for target in targets:


            if rules.is_allowed(target):

                valid_targets.append(
                    target
                )


        if not valid_targets:

            return None


        # Por ahora:
        # el más cercano

        return min(
            valid_targets,
            key=lambda x:x.distance
        )