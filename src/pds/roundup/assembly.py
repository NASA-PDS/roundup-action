# encoding: utf-8

'''🤠 PDS Roundup: Assemblies. An assembly is responsible for conducting the roundup.'''

from .step import StepName
import logging

_logger = logging.getLogger(__name__)


class Assembly(object):
    '''Generic assembly whose job is to do a roundup; subclasses provide refined assembly
    behavior.
    '''
    def __init__(self, context, stepNames=[]):
        '''Assemblies have a ``context`` that tells the morphology (location and environment) of
        the roundup and the names of the steps (``stepNames``) they'll need to do
        .'''
        self.context, self.stepNames = context, stepNames

    def __repr__(self):
        return f'<{self.__class__.__name__}(context={self.context},#stepNames={len(self.stepNames)})>'

    def roundup(self):
        '''Round 'em up, pardner! 🤠'''
        _logger.debug('🤠 Preparing roundup for %r with the following steps: %r', self.context, self.stepNames)
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
        '''By default, assemblies will always be for "unstable" or in-development releases, so this
        always returns False. Subclasses might override this.
        '''
        return False

    # 🤔 Other characteristics of the assembly can go here. For example, we might replace
    # ``isStable`` (which isn't very "OO") with methods that return attributes of the assembly
    # like "what PyPI do I use" and "how do we mark a snapshot", etc.


class NoOpAssembly(Assembly):
    '''A special assembly that does nothing but using a single step, namely ``StepName.null``.'''
    def __init__(self, context):
        super(NoOpAssembly, self).__init__(context, [StepName.null])


class PDSAssembly(Assembly):
    '''The PDS-flavored assembly which has 9 different steps'''
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
    '''The stable (production) PDS assembly'''
    def isStable(self):
        return True


class UnstablePDSAssembly(PDSAssembly):
    '''The unstable (in-development) PDS assembly'''
    pass
