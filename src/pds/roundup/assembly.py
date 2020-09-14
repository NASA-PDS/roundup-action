# encoding: utf-8


from .step import StepName
import logging

_logger = logging.getLogger(__name__)


class Assembly(object):
    def __init__(self, context, stepNames=[]):
        self.context, self.stepNames = context, stepNames

    def __repr__(self):
        return f'<{self.__class__.__name__}(context={self.context},#stepNames={len(self.stepNames)})>'

    def roundup(self):
        _logger.debug('Preparing roundup for %r with the following steps: %r', self.context, self.stepNames)
        steps = []
        for stepName in self.stepNames:
            step = self.context.createStep(stepName, self)
            if step:
                steps.append(step)
            else:
                _logger.info('For context %r no step was available for %s; ignoring this step', self.context, stepName)
        _logger.debug('Executing roundup')
        for step in steps:
            step.execute()

    def isStable(self):
        return False


class NoOpAssembly(Assembly):
    def __init__(self, context):
        super(NoOpAssembly, self).__init__(context, [StepName.null])


class PDSAssembly(Assembly):
    pdsSteps = [
        StepName.unitTest,
        StepName.integrationTest,
        StepName.changeLog,
        StepName.requirements,
        StepName.docs,
        StepName.build,
        StepName.githubRelease,
        StepName.artifactPublication,
        StepName.docPublication,
    ]

    def __init__(self, context):
        super(PDSAssembly, self).__init__(context, self.pdsSteps)


class StablePDSAssembly(PDSAssembly):
    def isStable(self):
        return True


class UnstablePDSAssembly(PDSAssembly):
    pass
