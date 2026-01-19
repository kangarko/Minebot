package org.mineacademy.minebridge.core.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.mineacademy.minebridge.core.internal.BaseSchema;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@Repeatable(WebSocketActions.class)
public @interface WebSocketAction {
    String value(); // The action name

    Class<? extends BaseSchema> schema() default BaseSchema.class;
}
